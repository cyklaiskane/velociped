import logging
import timeit
import shapely.wkt
import asyncio
from typing import List, Dict, Tuple
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from devtools import debug
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from asyncpg import create_pool

from api.utils import get_db, pairwise, find_route
from api.config import POSTGRES_DSN, LM_CLIENT_ID, LM_CLIENT_SECRET, LM_TOKEN_URL
from api.security import fetch_token, update_token


app = FastAPI()

oauth = OAuth(fetch_token=fetch_token, update_token=update_token)

oauth.register(
    'lm',
    client_id=str(LM_CLIENT_ID),
    client_secret=str(LM_CLIENT_SECRET),
    access_token_url=LM_TOKEN_URL,
    client_kwargs={'grant_type': 'client_credentials'},
    api_base_url='http://localhost:8000/api',
)

#app.add_middleware(
#    SessionMiddleware,
#    secret_key='should-be-random'
#)

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


@app.get('/foo')
async def foo(request: Request):
    logging.debug(request.headers)


@app.get('/api/address/{text}')
async def address_search(text: str, request: Request):
    lm = oauth.lm
    await lm.get('http://localhost:8000/foo', request=request)


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
async def route(query: RouteQuery, request: Request):
    debug(query)
    routes = []

    results = await asyncio.gather(*[do_route(request.app.db, query.waypoints, name, profile) for name, profile in [('Lämpligast', 1), ('Snabbast', 0), ('Säkrast', 2)]])
    for route in results:
        routes.append(route)
    return routes

async def do_route(db, waypoints, name, profile):
    route = Route(name=name)

    results = await asyncio.gather(*[find_route(db, start, dest, profile=profile) for start, dest in pairwise(waypoints)])

    for result in results:
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

    return route


@app.on_event('startup')
async def startup():
    async def init_con(con):
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

    app.db = await create_pool(dsn=POSTGRES_DSN, min_size=10, max_size=20, init=init_con)


@app.on_event('shutdown')
async def shutdown():
    await app.db.close()


def main():
    import uvicorn
    uvicorn.run('api.main:app', host='0.0.0.0', reload=True, log_level='debug')


if __name__ == '__main__':
    main()
