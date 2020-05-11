import logging
import shapely.geometry
import shapely.wkb
from devtools import debug
from itertools import tee

from fastapi import Request


async def get_db(request: Request):
    async with request.app.db.acquire() as con:
        def encode_geometry(geometry):
            if not hasattr(geometry, '__geo_interface'):
                raise TypeError(f'{geometry} does not conform to the '
                                'geo intergace')
            shape = shapely.geometry.asShape(geometry)
            return shapely.wkb.dumps(shape)

        def decode_geometry(wkb):
            return shapely.wkb.loads(wkb)

        await con.set_type_codec(
            'geometry',
            encoder=encode_geometry,
            decoder=decode_geometry,
            format='binary'
        )
        yield con


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


async def find_route(db, start, dest):
    waypoints_sql = []
    for i, waypoint in enumerate([start, dest]):
        waypoints_sql.append(f'({i}, ST_Transform(ST_SetSRID(ST_MakePoint('
                             f'{waypoint.lng}, {waypoint.lat})'
                             ', 4326), 3006))')

    inner_sql = f'''
        WITH waypoints(id, geom) AS (
            VALUES {','.join(waypoints_sql)}
        ), path(geom) AS (
            SELECT ST_MakeLine(geom) FROM waypoints
        ), weights(ts_klass, weight) AS (
            VALUES
                ('C1', 1), ('C2', 1.1), ('C3', 1.1),
                ('B1', 1.2), ('B2', 1.3), ('B3', 1.5), ('B4', 1.9), ('B5', -1),
                ('G1', 1.4), ('G2', 1.6)
        )
        SELECT
            objectid as id,
            from_vertex as source,
            to_vertex as target,
            shape_length * COALESCE(weight, -1) as cost
        FROM cyklaiskane roads
        JOIN path ON ST_DWithin(roads.geom, path.geom, 5000)
        JOIN weights USING (ts_klass)
    '''

    sql = f'''
        WITH waypoints(id, geom) AS (
            VALUES {','.join(waypoints_sql)}
        ), vias AS (
            SELECT
                point.id waypoint_id,
                nearest.objectid,
                nearest.fraction
            FROM waypoints point,
            LATERAL (
                SELECT
                  ST_LineLocatePoint(roads.geom, point.geom) fraction, roads.*
                FROM (
                  SELECT *
                  FROM cyklaiskane
                  ORDER BY geom <-> point.geom ASC LIMIT 10
                ) roads
                ORDER BY ST_Distance(roads.geom, point.geom) ASC
                LIMIT 1
            ) nearest
        )
        SELECT
            roads.objectid,
            roads.ts_klass,
            roads.from_vertex,
            roads.to_vertex,
            roads.shape_length,
            vias.waypoint_id,
            vias.fraction,
            CASE WHEN vias.fraction IS NULL THEN 'full length' ELSE 'snip snip' END as bar,
            route.*,
            lead(route.id1) over () as route_to_vertex,
            route.id1 != roads.from_vertex AND coalesce(lead(route.id1) over (), -1) != roads.to_vertex as reverse,
            CASE WHEN route.id1 = roads.from_vertex OR coalesce(lead(route.id1) over (), -1) = roads.to_vertex THEN 'go ahead!' ELSE 'reverse!' END as foo,
            ST_Transform(
                CASE WHEN route.id1 = roads.from_vertex OR coalesce(lead(route.id1) over (), -1) = roads.to_vertex THEN
                    CASE
                    WHEN vias.fraction IS NULL THEN roads.geom
                    WHEN route.id1 = -1 THEN ST_LineSubstring(roads.geom, vias.fraction, 1)
                    ELSE ST_LineSubstring(roads.geom, 0, vias.fraction)
                    END
                ELSE
                    ST_Reverse(
                        CASE
                        WHEN vias.fraction IS NULL THEN roads.geom
                        WHEN route.id1 = -1 THEN ST_LineSubstring(roads.geom, 0, vias.fraction)
                        ELSE ST_LineSubstring(roads.geom, vias.fraction, 1)
                        END
                    )
                END,
                4326
            ) as geom
        FROM pgr_trsp(
            '{inner_sql.replace("'", "''")}',
            (SELECT array_agg(objectid) FROM vias)[1],
            (SELECT array_agg(fraction) FROM vias)[1],
            (SELECT array_agg(objectid) FROM vias)[2],
            (SELECT array_agg(fraction) FROM vias)[2],
            FALSE,
            FALSE,
            'SELECT * FROM cyklaiskane_restrictions'
        ) route
        JOIN cyklaiskane roads ON route.id2 = roads.objectid
        LEFT OUTER JOIN vias USING (objectid)
        ORDER BY route.seq
    '''
    logging.debug(sql)

    return await db.fetch(sql)
