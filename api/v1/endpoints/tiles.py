from fastapi import APIRouter, Request, Response
import logging
from api.database import db

router = APIRouter()


@router.api_route('/ts.json', methods=['GET', 'HEAD'])
def tilejson(request: Request) -> dict:
    base_url = request.base_url
    return {
        'tilejson': '2.2.0',
        'name': 'tsnet',
        'description': 'Trafiksäkerhetsklassat vägnät',
        'tiles': [str(base_url) + 'tiles/{z}/{x}/{y}.pbf'],
    }


@router.get('/ts/{z}/{x}/{y}.pbf')
async def tile(z: int, x: int, y: int) -> Response:
    resolution = 40075016.68557849 / (256 * 2 ** z)
    logging.debug(resolution)
    sql = f'''
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

    tile = await db.fetch_val(sql, column='tile')

    return Response(content=tile, media_type='application/x-protobuf')
