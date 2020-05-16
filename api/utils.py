import logging
import shapely.geometry
import shapely.wkb
from devtools import debug
from itertools import tee

from fastapi import Request


async def get_db(request: Request):
    async with request.app.db.acquire() as con:
        yield con


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def weights(n):
    names = ['C1', 'C2', 'C3', 'B1', 'B2', 'B3', 'B4', 'B5', 'G1', 'G2']
    speeds = [18, 15, 18, 18, 18, 18, 18, 1, 15, 13]
    weights = [
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.1, -1, 1.2, 1.2],
        [1.0, 1.1, 1.1, 1.2, 1.3, 1.5, 1.9, -1, 1.4, 1.6],
        [1.0, 1.1, 1.1, 1.2, 1.3, 8.0, 10., -1, 1.4, 1.6]
    ]

    tmp = [(n, w * 3.6 / s, w) for n, w, s in zip(names, weights[n], speeds)]
    return tmp


async def find_route(db, start, dest, profile=1):
    waypoints_sql = []
    for i, waypoint in enumerate([start, dest]):
        waypoints_sql.append(f'({i}, ST_Transform(ST_SetSRID(ST_MakePoint('
                             f'{waypoint.lng}, {waypoint.lat})'
                             ', 4326), 3006))')

    weights_sql = ', '.join([f"('{n}', {w}, {p})" for n, w, p in weights(profile)])

    inner_sql = f'''
        WITH waypoints(id, geom) AS (
            VALUES {','.join(waypoints_sql)}
        ), path AS (
            SELECT
                ST_MakeLine(geom) AS geom,
                least(greatest(ST_Length(ST_MakeLine(geom)) * 0.2, 1000), 5000) AS limit
            FROM waypoints
        ), weights(ts_klass, weight, penalty) AS (
            VALUES {weights_sql}
        )
        SELECT
            objectid as id,
            from_vertex as source,
            to_vertex as target,
            CASE WHEN weight IS NOT NULL AND f_forbjuden_fardriktning IS NULL THEN shape_length * weight ELSE -1 END as cost,
            CASE WHEN weight IS NOT NULL AND b_forbjuden_fardriktning IS NULL THEN shape_length * weight ELSE -1 END as reverse_cost
        FROM cyklaiskane roads
        JOIN path ON ST_DWithin(roads.geom, path.geom, path.limit)
        JOIN weights USING (ts_klass)
    '''

    sql = f'''
        WITH waypoints(id, geom) AS (
            VALUES {','.join(waypoints_sql)}
        ), weights(ts_klass, weight, penalty) AS (
            VALUES {weights_sql}
        ), vias AS (
            SELECT
                point.id waypoint_id,
                nearest.objectid,
                nearest.fraction,
                ST_LineInterpolatePoint(nearest.geom, nearest.fraction) geom
            FROM waypoints point,
            LATERAL (
                SELECT
                  ST_LineLocatePoint(roads.geom, point.geom) fraction, roads.*
                FROM (
                  SELECT *
                  FROM cyklaiskane
                  JOIN weights USING (ts_klass)
                  WHERE weights.weight > 0
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
            roads.namn_130 as name,
            route.cost / weights.weight as length,
            route.cost / weights.penalty as duration,
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
            TRUE,
            TRUE,
            'SELECT * FROM cyklaiskane_restrictions'
        ) route
        JOIN cyklaiskane roads ON route.id2 = roads.objectid
        JOIN weights USING (ts_klass)
        LEFT OUTER JOIN vias USING (objectid)
        ORDER BY route.seq
    '''
    logging.debug(sql)

    return await db.fetch(sql)
