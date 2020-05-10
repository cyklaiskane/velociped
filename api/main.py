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

    statement = await db.prepare('''
        SELECT
          objectid,
          ts_klass,
          shape_length,
          from_vertex,
          to_vertex,
          ST_StartPoint(geom) from_vertex_geom,
          ST_EndPoint(geom) to_vertex_geom,
          geom,
          fraction,
          point_geom,
          ST_LineInterpolatePoint(geom, fraction) virtual_vertex_geom
        FROM
          ST_Transform(ST_SetSRID(ST_MakePoint($1, $2), 4326), 3006) point_geom,
        LATERAL (
          SELECT
            ST_LineLocatePoint(roads.geom, point_geom) fraction, roads.*
          FROM (
            SELECT * FROM cyklaiskane ORDER BY geom <-> point_geom ASC LIMIT 10
          ) roads
          ORDER BY ST_Distance(roads.geom, point_geom) ASC
          LIMIT 1
        ) nearest;
    ''')

    waypoints = []
    for waypoint in query.waypoints:
        debug(waypoint)
        waypoints.append(await statement.fetchrow(*waypoint.to_xy()))

    debug(waypoints)

    sql = '''
        SELECT
            c.objectid,
            c.ts_klass,
            c.from_vertex,
            c.to_vertex,
            c.shape_length,
            r.*,
            ST_Transform(CASE WHEN r.id1 = c.from_vertex THEN geom ELSE ST_Reverse(geom) END, 4326) as geom
        FROM pgr_trsp('{sql}'::text, {from_vertex}, {to_vertex}, FALSE, FALSE, '{restrict_sql}') r
        JOIN (
            SELECT
                objectid,
                ts_klass,
                shape_length,
                from_vertex,
                to_vertex,
                geom
            FROM cyklaiskane
            {union_sql}
        ) c ON r.id2 = c.objectid
        ORDER BY r.seq
    '''

    rsql = '''
        SELECT * FROM cyklaiskane_restrictions
    '''

    sql3 = '''
        SELECT
            {objectid}::integer objectid,
            '{ts_klass}' ts_klass,
            {shape_length}::float shape_length,
            {from_vertex}::integer from_vertex,
            {to_vertex}::integer to_vertex,
            ST_LineSubstring(ST_GeomFromText('{geom}', 3006), {from_frac}, {to_frac}) geom
    '''

    wpt_sql = []
    wpt_vertex = []
    virtual_object_id = -9000
    for i, wpt in enumerate(waypoints, start=9000):
        frac = wpt['fraction']
        if frac < 0.001:
            wpt_vertex.append(wpt['from_vertex'])
        elif frac > 0.999:
            wpt_vertex.append(wpt['to_vertex'])
        else:
            wpt_vertex.append(-i)
        res1 = sql3.format(objectid=virtual_object_id, ts_klass=wpt['ts_klass'],
                           shape_length=wpt['shape_length'] * frac,
                           from_vertex=wpt['from_vertex'],
                           to_vertex=-i,
                           geom=shapely.wkt.dumps(wpt['geom']),
                           from_frac=0.0, to_frac=frac)
        virtual_object_id -= 1
        res2 = sql3.format(objectid=virtual_object_id, ts_klass=wpt['ts_klass'],
                           shape_length=wpt['shape_length'] * (1 - frac),
                           from_vertex=-i,
                           to_vertex=wpt['to_vertex'],
                           geom=shapely.wkt.dumps(wpt['geom']),
                           from_frac=frac, to_frac=1.0)
        virtual_object_id -= 1

        wpt_sql.append(f'''
        {res1}
        UNION ALL
        {res2}
        ''')
        debug(wpt_sql[-1])
    debug(wpt_vertex)

    sql2 = '''
        WITH q AS (
            SELECT
                ST_MakeLine(ST_GeomFromText('{0}', 3006), ST_GeomFromText('{1}', 3006)) line
        ), w(ts_klass, weight) AS (
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
        FROM (
            SELECT
                objectid,
                ts_klass,
                shape_length,
                from_vertex,
                to_vertex,
                geom
            FROM cyklaiskane
            JOIN q ON ST_DWithin(geom, q.line, 5000)
            {union_sql}
        ) c
        JOIN w ON c.ts_klass = w.ts_klass
    '''
    union_sql = '' if len(wpt_sql) == 0 else 'UNION ALL\n' + '\nUNION ALL\n'.join(wpt_sql)
    logging.debug(union_sql)
    sql2_res = sql2.format(shapely.wkt.dumps(waypoints[0]['virtual_vertex_geom']),
               shapely.wkt.dumps(waypoints[-1]['virtual_vertex_geom']),
               union_sql=union_sql)

    sql_final = sql.format(sql=sql2_res.replace("'", "''"), from_vertex=wpt_vertex[0],
                           to_vertex=wpt_vertex[-1], union_sql=union_sql, restrict_sql=rsql)
    logging.debug(sql_final)
    result = await db.fetch(sql_final)

    routes = []
    route = None
    for row in result:
        if row['seq'] == 0:
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
