import asyncio
import logging
from typing import Any, List

from authlib.integrations.starlette_client import OAuth
from devtools import debug
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from api.config import CORS_ORIGINS, LM_CLIENT_ID, LM_CLIENT_SECRET, LM_TOKEN_URL
from api.database import db
from api.schemas import LatLng, Route, RouteQuery, Segment
from api.security import fetch_token, update_token
from api.utils import find_route, pairwise

app = FastAPI()

oauth = OAuth(fetch_token=fetch_token, update_token=update_token)

oauth.register(
    "lm",
    client_id=str(LM_CLIENT_ID),
    client_secret=str(LM_CLIENT_SECRET),
    access_token_url=LM_TOKEN_URL,
    client_kwargs={"grant_type": "client_credentials"},
    api_base_url="http://localhost:8000/api",
)

# app.add_middleware(
#    SessionMiddleware,
#    secret_key='should-be-random'
# )

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = []
for origin in CORS_ORIGINS:
    use_origin = origin.strip()
    origins.append(use_origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def index(request: Request) -> Any:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/foo")
async def foo(request: Request) -> None:
    logging.debug(request.headers)


@app.get("/api/address/{text}")
async def address_search(text: str, request: Request) -> None:
    lm = oauth.lm
    await lm.get("http://localhost:8000/foo", request=request)


@app.get("/items")
async def get_items() -> List:
    items = await db.fetch_all("SELECT * FROM cyklaiskane LIMIT 10")
    for item in items:
        debug(item)
    return items


@app.head("/tiles.json")
@app.get("/tiles.json")
def tilejson() -> dict:
    return {
        "tilejson": "2.2.0",
        "name": "Cyklaiskåne",
        "description": "Foobar",
        "tiles": ["http://localhost:8000/tiles/{z}/{x}/{y}.pbf"],
    }


@app.get("/tiles/{z}/{x}/{y}.pbf")
async def tile(z: int, x: int, y: int) -> Response:
    resolution = 40075016.68557849 / (256 * 2 ** z)
    logging.debug(resolution)
    sql = f"""
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
    """

    tile = await db.fetch_val(sql, column="tile")

    return Response(content=tile, media_type="application/x-protobuf")


@app.post("/api/point")
async def point(latlng: LatLng) -> List:
    logging.debug(latlng)
    result = await db.fetch_all(
        """
        SELECT ST_AsGeoJSON(ST_Transform(geom, 4326))
        FROM cyklaiskane
        WHERE ST_DWithin(
            ST_Transform(ST_SetSRID(ST_MakePoint(:x, :y), 4326), 3006),
            geom,
            100
        )
    """,
        {"x": latlng.lng, "y": latlng.lat},
    )
    logging.debug(result)
    return result


@app.post("/api/route")
async def route(query: RouteQuery, request: Request) -> List:
    debug(query)
    routes = []

    results = await asyncio.gather(
        *[
            do_route(query.waypoints, name, profile)
            for name, profile in [("Lämpligast", 1), ("Snabbast", 0), ("Säkrast", 2)]
        ]
    )
    for route in results:
        routes.append(route)
    return routes


async def do_route(waypoints: List, name: str, profile: int) -> Route:
    route = Route(name=name)

    results = await asyncio.gather(
        *[
            find_route(start, dest, profile=profile)
            for start, dest in pairwise(waypoints)
        ]
    )

    for result in results:
        for row in result:
            if row["waypoint_id"] is not None:
                debug(row)
            segment = Segment(
                coords=row["geom"].coords[:],
                name=row["name"],
                ts_klass=row["ts_klass"],
                length=row["length"],
                duration=row["duration"],
            )
            route.length += segment.length
            route.duration += segment.duration
            route.segments.append(segment)

    return route


@app.on_event("startup")
async def startup() -> None:
    await db.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    await db.disconnect()


def main() -> None:
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", reload=True, log_level="debug")


if __name__ == "__main__":
    main()
