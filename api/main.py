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

from api.utils import get_db, pairwise, find_route
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
    name: str = None
    ts_klass: str
    length: float
    duration: float


class Route(BaseModel):
    name: str = ''
    length: float = 0.0
    duration: float = 0.0
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
    routes = []

    for name, i in [('Lämpligast', 1), ('Snabbast', 0), ('Säkrast', 2)]:
        route = Route(name=name)

        for start, dest in pairwise(query.waypoints):
            debug(start, dest)

            result = await find_route(db, start, dest, profile=i)

            for row in result:
                if row['waypoint_id'] is not None:
                    debug(row)
                segment = Segment(coords=row['geom'].coords[:],
                                  name=row['name'],
                                  ts_klass=row['ts_klass'],
                                  length=row['length'],
                                  duration=row['duration'])
                route.length += segment.length
                route.duration += segment.duration
                route.segments.append(segment)
        #debug(routes)
        routes.append(route)
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
