import asyncio
import logging
from typing import List, Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.schemas import Route, RouteQuery, Segment
from api.utils import pairwise
from api.v1.utils import find_route

router = APIRouter()


@router.post('')
async def route(query: RouteQuery, request: Request) -> Union[List, JSONResponse]:
    routes = []

    try:
        results = await asyncio.gather(
            *[
                do_route(query.waypoints, name, profile)
                for name, profile in [
                    ('Lämpligast', 1)
                ]  # [('Lämpligast', 1), ('Snabbast', 0), ('Säkrast', 2)]
            ]
        )
    except Exception as e:
        logging.warn(e)
        return JSONResponse(content={'error': str(e)}, status_code=500)
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
            segment = Segment(
                coords=row['geom'].coords[:],
                name=row['name'],
                ts_klass=row['ts_klass'],
                length=row['length'],
                duration=row['duration'],
            )
            route.length += segment.length
            route.duration += segment.duration
            route.segments.append(segment)

    return route
