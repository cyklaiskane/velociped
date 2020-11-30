import logging
from datetime import datetime
from itertools import tee
from typing import Iterable

from osgeo import gdal, ogr, osr

from api.config import GEODATA_LAYER, GEODATA_TABLE, GEODATA_URL, POSTGRES_DSN


def pairwise(iterable: Iterable) -> Iterable:
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def update_geodata() -> None:
    now = datetime.utcnow().strftime('%Y_%m_%d_%H%M%S_%f')
    dst_table = f'{GEODATA_TABLE}_{now}'
    pgr_table = f'{dst_table}_vertices_pgr'
    restr_table = f'{dst_table}_restrictions'
    logging.getLogger().setLevel('DEBUG')

    gdal.UseExceptions()
    gdal.SetConfigOption('OGR_WFS_PAGING_ALLOWED', 'NO')

    src_ds = gdal.OpenEx(
        GEODATA_URL,
        0,
        open_options=['EXPOSE_GML_ID=NO']
        if GEODATA_URL.lower().startswith('wfs:')
        else [],
    )
    src_layer = src_ds.GetLayerByName(GEODATA_LAYER)
    src_layer.SetSpatialFilterRect(396181.4, 6169076.0, 396994.0, 6169484.3)

    schema = {
        'objectid': ogr.OFTInteger,
        'ts_klass': ogr.OFTString,
        'namn_130': ogr.OFTString,
        'klass_181': ogr.OFTInteger,
        'konst_190': ogr.OFTString,
        'shape_length': ogr.OFTReal,
        'from_vertex': ogr.OFTInteger,
        'to_vertex': ogr.OFTInteger,
    }
    src_fields = [item.GetName() for item in src_layer.schema]
    src_ignore = [name for name in src_fields if name.lower() not in schema]
    common_fields = [
        (name, name.lower()) for name in src_fields if name.lower() in schema
    ]

    src_layer.SetIgnoredFields(src_ignore)
    src_len = len(src_layer)
    step = src_len // 20

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3006)
    dst_ds = ogr.Open(
        f'PG:host={POSTGRES_DSN.hostname} dbname={POSTGRES_DSN.database} user={POSTGRES_DSN.username} password={POSTGRES_DSN.password}'
    )
    dst_ds.StartTransaction()
    dst_layer = dst_ds.CreateLayer(
        dst_table,
        srs=srs,
        geom_type=ogr.wkbLineString,
        options=[
            'GEOMETRY_NAME=geom',
            'DIM=2',
            'OVERWRITE=YES',
            'SPATIAL_INDEX=SPGIST',
        ],
    )

    for name, dtype in schema.items():
        dst_layer.CreateField(ogr.FieldDefn(name, dtype))

    logging.info(f'Copying {src_len} features from geodata source {GEODATA_URL}')
    for i, src_feature in enumerate(src_layer, 1):
        if i % step == 1:
            logging.info(
                f'Feature copy progress {i:8d} / {src_len}, {100*i/src_len:5.2f} %'
            )
        dst_feature = ogr.Feature(dst_layer.GetLayerDefn())
        for src_field, dst_field in common_fields:
            dst_feature[dst_field] = src_feature[src_field]
        dst_feature.SetGeometry(src_feature.GetGeometryRef())
        dst_layer.CreateFeature(dst_feature)
        dst_feature = None

    pgr_sql = f'''
        SELECT pgr_createTopology(
            '{dst_table}',
            0.1,
            'geom',
            'objectid',
            'from_vertex',
            'to_vertex',
            'true',
            true
        )
    '''
    logging.info('Building PGR topology')
    result = dst_ds.ExecuteSQL(pgr_sql)
    status = result.GetNextFeature().GetFieldAsString(0)
    dst_ds.ReleaseResultSet(result)
    if status != 'OK':
        dst_ds.RollbackTransaction()
        raise Exception('Failed to build PGR topology')
    logging.info('Building restrictions')
    restr_sql = f'''
        CREATE TABLE {restr_table} (to_cost, target_id, via_path) AS
        WITH grades AS (
          SELECT
            objectid,
            konst_190,
            ARRAY[from_vertex, to_vertex] as vertices
          FROM {dst_table} WHERE konst_190 IS NOT NULL
        )
        SELECT
          1000::float8 to_cost,
          a.objectid::int4 target_id,
          b.objectid::text via_path
        FROM grades a, grades b
        WHERE a.konst_190 != b.konst_190 AND a.vertices && b.vertices;
    '''
    dst_ds.ExecuteSQL(restr_sql)
    dst_ds.ExecuteSQL(f'CREATE INDEX ON {restr_table} (target_id)')
    dst_ds.CommitTransaction()

    logging.info('Replacing geodata tables')
    dst_ds.StartTransaction()
    dst_ds.ExecuteSQL(f'DROP TABLE IF EXISTS {GEODATA_TABLE} CASCADE')
    dst_ds.ExecuteSQL(f'ALTER TABLE {dst_table} RENAME TO {GEODATA_TABLE}')
    dst_ds.ExecuteSQL(f'DROP TABLE IF EXISTS {GEODATA_TABLE}_vertices_pgr CASCADE')
    dst_ds.ExecuteSQL(f'ALTER TABLE {pgr_table} RENAME TO {GEODATA_TABLE}_vertices_pgr')
    dst_ds.ExecuteSQL(f'DROP TABLE IF EXISTS {GEODATA_TABLE}_restrictions CASCADE')
    dst_ds.ExecuteSQL(
        f'ALTER TABLE {restr_table} RENAME TO {GEODATA_TABLE}_restrictions'
    )
    dst_ds.CommitTransaction()

    logging.info('Cleaning up database')
    dst_ds.ExecuteSQL('VACUUM ANALYZE')

    dst_layer = None
    dst_ds = None
    src_layer = None
    src_ds = None
