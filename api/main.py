import logging
import timeit
import shapely.wkt
from typing import List, Dict, Tuple
from fastapi import FastAPI, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from devtools import debug
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from asyncpg import create_pool

from api.utils import get_db
from api.config import POSTGRES_DSN


app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')

CORS_ORIGINS = '*'
origins = []
if CORS_ORIGINS:
    origins_raw = CORS_ORIGINS.split(',')
    for origin in origins_raw:
        use_origin = origin.strip()
        origins.append(use_origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),

templates = Jinja2Templates(directory='templates')


@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/items')
async def get_items(db=Depends(get_db)):
    logging.debug(await db.fetch('SELECT * FROM cyklaiskane LIMIT 10'))


class LatLng(BaseModel):
    lat: float
    lng: float

    def to_xy(self):
        return [self.lng, self.lat]


class RouteQuery(BaseModel):
    waypoints: List[LatLng]


class Segment(BaseModel):
    coords: List[Tuple[float, float]]


class Route(BaseModel):
    segments: List[Segment] = []


@app.post('/api/point')
async def point(latlng: LatLng, db=Depends(get_db)):
    logging.debug(latlng)
    result = await db.fetch('''
        SELECT ST_AsGeoJSON(ST_Transform(geom, 4326))
        FROM cyklaiskane
        WHERE ST_DWithin(ST_Transform(ST_SetSRID(ST_MakePoint($1, $2), 4326), 3006), geom, 100)
    ''', *latlng.to_xy())
    logging.debug(result)
    return result


@app.post('/api/route')
async def route(query: RouteQuery, db=Depends(get_db)):
    debug(query)

    waypoints_sql = []
    for i, waypoint in enumerate(query.waypoints):
        waypoints_sql.append(f'({i}, ST_Transform(ST_SetSRID(ST_MakePoint('
                             f'{waypoint.lng}, {waypoint.lat})'
                             ', 4326), 3006))')
    debug(waypoints_sql)

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

    route_sql = f'''
        WITH waypoints(id, geom) AS (
            VALUES {','.join(waypoints_sql)}
        ), vias AS (
            SELECT
                point.id,
                nearest.objectid,
                nearest.fraction
            FROM waypoints point,
            LATERAL (
                SELECT
                  ST_LineLocatePoint(roads.geom, point.geom) fraction, roads.*
                FROM (
                  SELECT * FROM cyklaiskane ORDER BY geom <-> point.geom ASC LIMIT 10
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
            vias.id,
            vias.fraction,
            route.*,
            ST_Transform(CASE WHEN route.id2 = roads.from_vertex THEN geom ELSE ST_Reverse(geom) END, 4326) as geom
        FROM pgr_trspViaEdges('{inner_sql.replace("'", "''")}', (SELECT array_agg(objectid) FROM vias), (SELECT array_agg(fraction) FROM vias), FALSE, FALSE, 'SELECT * FROM cyklaiskane_restrictions') route
        JOIN cyklaiskane roads ON route.id3 = roads.objectid
        LEFT OUTER JOIN vias USING (objectid)
        ORDER BY route.seq
    '''
    logging.debug(route_sql)

    result = await db.fetch(route_sql)

    routes = []
    route = None
    for row in result:
        if row['seq'] == 1:
            route = Route()
            routes.append(route)
        #logging.debug(row['geom'].coords[:])
        debug(row)
        segment = Segment(coords=row['geom'].coords[:])
        route.segments.append(segment)
    #debug(routes)
    return routes




@app.on_event('startup')
async def startup():
    app.db = await create_pool(dsn=POSTGRES_DSN, min_size=5, max_size=10)


@app.on_event('shutdown')
async def shutdown():
    await app.db.close()


def main():
    import uvicorn
    uvicorn.run('api.main:app', host='0.0.0.0', reload=True, log_level='debug')


if __name__ == '__main__':
    main()
