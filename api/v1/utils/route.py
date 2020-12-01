import json
import logging
from typing import Iterable, List, Optional

from api.database import db
from api.schemas import LatLng, RouteProfile


class ProfileStore:
    store: List[RouteProfile] = []

    def load(self, filename: str) -> None:
        items = []
        with open(filename, 'r') as f:
            items = json.load(f)

        for item in items:
            self.store.append(RouteProfile(**item))

    def get(self, name: Optional[str] = None) -> RouteProfile:
        for profile in self.store:
            if name == profile.name:
                return profile
        return self.store[0]


profiles = ProfileStore()


def weights(profile: RouteProfile) -> list:
    speeds = profile.speeds.dict()
    weights = profile.weights.dict()

    tmp = [
        (klass, weight * 3.6 / speeds[klass], weight)
        for klass, weight in weights.items()
    ]
    return tmp


async def find_route(start: LatLng, dest: LatLng, profile: RouteProfile) -> Iterable:
    waypoints_sql = []
    for i, waypoint in enumerate([start, dest]):
        waypoints_sql.append(
            f'({i}, ST_Transform(ST_SetSRID(ST_MakePoint('
            f'{waypoint.lng}, {waypoint.lat})'
            ', 4326), 3006))'
        )

    weights_sql = ', '.join([f"('{n}', {w}, {p})" for n, w, p in weights(profile)])

    inner_sql = f'''
        WITH waypoints(id, geom) AS (
            VALUES {','.join(waypoints_sql)}
        ), path AS (
            SELECT
                ST_MakeLine(geom) AS geom,
                least(greatest(ST_Length(ST_MakeLine(geom)) * 0.4, 2000), 10000) AS limit
            FROM waypoints
        ), weights(ts_klass, weight, penalty) AS (
            VALUES {weights_sql}
        )
        SELECT
            objectid as id,
            from_vertex as source,
            to_vertex as target,
            CASE
                WHEN weight IS NOT NULL AND f_forbjuden_fardriktning IS NULL
                THEN shape_length * weight
                ELSE -1
            END as cost,
            CASE WHEN weight IS NOT NULL AND b_forbjuden_fardriktning IS NULL
                THEN shape_length * weight
                ELSE -1
            END as reverse_cost
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
                point.id,
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
        ), from_point AS (
            SELECT * FROM vias WHERE id = 0 LIMIT 1
        ), to_point AS (
            SELECT * FROM vias WHERE id = 1 LIMIT 1
        ), parts AS (
            SELECT
                roads.objectid,
                roads.ts_klass,
                roads.from_vertex,
                roads.to_vertex,
                roads.shape_length,
                roads.namn_130 as name,
                route.cost / weights.weight as length,
                route.cost / weights.penalty as duration,
                from_point.id as from_point_id,
                from_point.fraction as from_fraction,
                to_point.id as to_point_id,
                to_point.fraction as to_fraction,
                route.*,
                lead(route.id1) over () as route_to_vertex,
                (
                    lag(ts_klass) OVER () IS DISTINCT FROM ts_klass
                    OR lag(namn_130) OVER () IS DISTINCT FROM namn_130
                )::int as part_start,
                CASE
                WHEN route.id1 = roads.from_vertex
                     OR lead(route.id1, 1, -1) OVER () = roads.to_vertex
                     OR (from_point.objectid = to_point.objectid
                         AND from_point.fraction < to_point.fraction)
                    THEN
                        CASE
                            WHEN COALESCE(from_point.fraction, to_point.fraction) IS NULL
                            THEN roads.geom
                            ELSE ST_LineSubstring(
                                roads.geom,
                                COALESCE(from_point.fraction, 0),
                                COALESCE(to_point.fraction, 1)
                            )
                        END
                ELSE
                    ST_Reverse(
                        CASE
                            WHEN COALESCE(from_point.fraction, to_point.fraction) IS NULL
                            THEN roads.geom
                            ELSE ST_LineSubstring(
                                roads.geom,
                                COALESCE(to_point.fraction, 0),
                                COALESCE(from_point.fraction, 1)
                            )
                        END
                    )
                END as geom
            FROM pgr_trsp(
                '{inner_sql.replace("'", "''")}',
                (SELECT objectid FROM from_point),
                (SELECT fraction FROM from_point),
                (SELECT objectid FROM to_point),
                (SELECT fraction FROM to_point),
                TRUE,
                TRUE,
                'SELECT to_cost, target_id, via_path FROM cyklaiskane_restrictions'
            ) route
            JOIN cyklaiskane roads ON route.id2 = roads.objectid
            JOIN weights USING (ts_klass)
            LEFT OUTER JOIN from_point USING (objectid)
            LEFT OUTER JOIN to_point USING (objectid)
            ORDER BY route.seq
        )
        SELECT
            array_agg(objectid ORDER BY seq) as ids,
            part,
            ts_klass,
            name,
            SUM(length) as length,
            SUM(duration) as duration,
            ST_Transform(ST_MakeLine(geom ORDER BY seq), 4326) as geom
        FROM (SELECT *, SUM(part_start) OVER (ORDER BY seq) part FROM parts) _
        GROUP BY part, ts_klass, name
        ORDER BY part
    '''
    logging.debug(sql)

    return await db.fetch_all(sql)
