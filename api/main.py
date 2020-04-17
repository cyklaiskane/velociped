import logging

from fastapi import FastAPI, Request, Depends, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from asyncpg import create_pool

from api.utils import get_db


app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')


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
        WITH q AS (
            SELECT ST_Transform(ST_SetSRID(ST_MakePoint({1}, {2}), 4326), 3006) source,
                   ST_Transform(ST_SetSRID(ST_MakePoint({3}, {4}), 4326), 3006) target
        ), start_ids AS (
            SELECT ARRAY (
                SELECT id
                FROM cyklaiskane_vertices_pgr JOIN q
                ON ST_DWithin(q.source, the_geom, 500)
                ORDER BY ST_Distance(q.source, the_geom) ASC
                LIMIT 2
            ) aid
        ), end_ids AS (
            SELECT ARRAY (
                SELECT id
                FROM cyklaiskane_vertices_pgr JOIN q
                ON ST_DWithin(q.target, the_geom, 500)
                ORDER BY ST_Distance(q.target, the_geom) ASC
                LIMIT 2
            ) aid
        )
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', json_agg(ST_AsGeoJSON(r.*)::json)
        ) json
        FROM (SELECT ST_Transform(geom, 4326) as geom FROM pgr_dijkstra({0}, (SELECT aid FROM start_ids), (SELECT aid FROM end_ids), FALSE) r
        JOIN cyklaiskane c ON r.edge = c.objectid) r
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
        )
        SELECT objectid as id, from_vertex as source, to_vertex as target, shape_length as cost
        FROM cyklaiskane c
        JOIN q
        ON ST_Dwithin(c.geom, q.line, 5000)'
    """.format(*query.start.to_xy(), *query.end.to_xy())
    result = await db.fetchrow(sql.format(sql2, *query.start.to_xy(), *query.end.to_xy()))
    logging.debug(result)
    return Response(content=result.get('json', None), media_type='application/json')




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
