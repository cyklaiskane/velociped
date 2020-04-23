import logging
from typing import List, Dict, Tuple
from fastapi import FastAPI, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from asyncpg import create_pool

from api.utils import get_db


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
    start: LatLng
    end: LatLng

class Segment(BaseModel):
    coords: List[Tuple[float,float]]

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
    logging.debug(query)
    sql = '''
        WITH start_ids AS (
            SELECT ARRAY (
                SELECT id
                FROM cyklaiskane_vertices_pgr
                ORDER BY the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({1}, {2}), 4326), 3006) ASC
                LIMIT 1
            ) aid
        ), end_ids AS (
            SELECT ARRAY (
                SELECT id
                FROM cyklaiskane_vertices_pgr
                ORDER BY the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({3}, {4}), 4326), 3006) ASC
                LIMIT 1
            ) aid
        )
        SELECT
            r.*,
            ST_Transform(CASE WHEN r.node = c.from_vertex THEN geom ELSE ST_Reverse(geom) END, 4326) as geom
        FROM pgr_dijkstra({0}, (SELECT aid FROM start_ids), (SELECT aid FROM end_ids), FALSE) r
        JOIN cyklaiskane c ON r.edge = c.objectid
        ORDER BY r.seq
    '''
    sql2 = """
        'WITH q AS (
            SELECT
                ST_Transform(
                    ST_SetSRID(
                        ST_MakeLine(ST_MakePoint({0}, {1}), ST_MakePoint({2}, {3})),
                        4326),
                    3006
                ) line
        ), w(ts_klass, weight) AS (
            VALUES
                (''C1'', 1), (''C2'', 1.1), (''C3'', 1.1),
                (''B1'', 1.2), (''B2'', 1.3), (''B3'', 1.5), (''B4'', 1.9), (''B5'', -1),
                (''G1'', 1.4), (''G2'', 1.6)
        )
        SELECT
            objectid as id,
            from_vertex as source,
            to_vertex as target,
            shape_length * COALESCE(weight, -1) as cost
        FROM cyklaiskane c
        JOIN q ON ST_DWithin(c.geom, q.line, 5000)
        JOIN w ON c.ts_klass = w.ts_klass'
    """.format(*query.start.to_xy(), *query.end.to_xy())

    result = await db.fetch(sql.format(sql2, *query.start.to_xy(), *query.end.to_xy()))

    routes = []
    route = None
    for row in result:
        if row['path_seq'] == 1:
            route = Route()
            routes.append(route)
        #logging.debug(row['geom'].coords[:])
        segment = Segment(coords=row['geom'].coords[:])
        route.segments.append(segment)

    return routes




@app.on_event('startup')
async def startup():
    app.db = await create_pool(dsn='postgres://velociped:foobar@localhost:5433/velociped',
                               min_size=5, max_size=10)


@app.on_event('shutdown')
async def shutdown():
    await app.db.close()


def main():
    import uvicorn
    uvicorn.run('api.main:app', host='0.0.0.0', reload=True, log_level='debug')


if __name__ == '__main__':
    main()
