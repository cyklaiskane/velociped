import logging

from fastapi import APIRouter, Request, Response, HTTPException

from api.database import db

from devtools import debug

router = APIRouter()


layers = {
    'ts': {
        'name': 'tsnet',
        'description': 'Trafiksäkerhetsklassat vägnät',
        'sql': '''
            WITH meta AS (
                SELECT
                    ST_TileEnvelope({z}, {x}, {y}) AS bounds,
                    ST_SRID(geom) AS srid
                FROM cyklaiskane LIMIT 1
            ), mvtgeom AS (
                SELECT * FROM meta,
                LATERAL (
                    SELECT
                        ST_AsMVTGeom(
                            ST_Transform(ST_Simplify(geom, {resolution}, TRUE), 3857),
                            meta.bounds,
                            4096,
                            256,
                            true
                        ) AS geom,
                        roads.ts_klass,
                        roads.klass_181
                    FROM cyklaiskane roads
                    WHERE
                        ST_Transform(meta.bounds, meta.srid) && roads.geom
                        AND (
                            ({z} > 10 AND ts_klass LIKE 'C%')
                            OR ({z} > 11 AND ts_klass LIKE 'G%')
                            OR (ts_klass LIKE 'B%')
                        )
                ) _ WHERE geom IS NOT NULL

            )
            SELECT ST_AsMVT(mvtgeom.*, 'roads', 4096, 'geom') AS tile FROM mvtgeom
        '''
    },
    'bg': {
        'name': 'background',
        'description': '',
        'sql': '''
            WITH mvtgeom AS (
                SELECT
                    ST_AsMVTGeom(
                        geom,
                        ST_TileEnvelope({z}, {x}, {y}),
                        4096,
                        256,
                        true
                    ) AS geom,
                    bg.kkod,
                    bg.kategori
                FROM background bg
                WHERE
                    ST_TileEnvelope({z}, {x}, {y}) && bg.geom
            )
            SELECT ST_AsMVT(mvtgeom.*, 'background', 4096, 'geom') AS tile FROM mvtgeom
        '''
    }
}


@router.api_route('/{layer}.json', methods=['GET', 'HEAD'])
def tilejson(layer: str, request: Request) -> dict:
    if layer not in layers:
        raise HTTPException(status_code=404, detail="Layer not found")
    url = request.url
    return {
        'tilejson': '2.2.0',
        'name': layers[layer]['name'],
        'description': layers[layer]['description'],
        'tiles': [str(url).replace('.json', '') + '/{z}/{x}/{y}.pbf'],
    }


@router.get('/{layer}/{z}/{x}/{y}.pbf')
async def tile(layer: str, z: int, x: int, y: int) -> Response:
    if layer not in layers:
        raise HTTPException(status_code=404, detail="Layer not found")
    resolution = 40075016.68557849 / (256 * 2 ** z)
    logging.debug(resolution)
    sql = layers[layer]['sql'].format(x=x, y=y, z=z, resolution=resolution)
    debug(sql)

    tile = await db.fetch_val(sql, column='tile')

    return Response(content=tile, media_type='application/x-protobuf')
