import asyncio
import logging
from typing import List, Union

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from api.schemas import Route, RouteProfile, RouteQuery, Segment
from api.utils import pairwise
from api.v1.utils.route import find_route, profiles

router = APIRouter()


@router.post('')
async def route(query: RouteQuery, request: Request) -> Union[List, JSONResponse]:
    routes = []

    try:
        results = await asyncio.gather(
            *[
                do_route(query.waypoints, profile)
                for profile in [profiles.get(query.profile_name)]
            ]
        )
    except Exception as e:
        logging.warn(e)
        return JSONResponse(content={'error': str(e)}, status_code=500)
    for route in results:
        routes.append(route)
    return routes


async def do_route(waypoints: List, profile: RouteProfile) -> Route:
    route = Route(name=profile.label)

    results = await asyncio.gather(
        *[
            find_route(start, dest, profile=profile)
            for start, dest in pairwise(waypoints)
        ]
    )

    for result in results:
        for row in result:
            danger_coords = []
            if row['danger_geom'] is not None:
                danger_coords.extend(
                    [point.coords[0] for point in row['danger_geom'].geoms]
                )
            segment = Segment(
                coords=row['geom'].coords[:],
                danger_coords=danger_coords,
                name=row['name'],
                ts_klass=row['ts_klass'],
                length=row['length'],
                duration=row['duration'],
            )
            route.length += segment.length
            route.duration += segment.duration
            route.segments.append(segment)

    return route


@router.get('/profiles')
async def get_profiles() -> List:
    print(profiles.store)
    return [
        profile.dict(include={'name', 'label', 'description'})
        for profile in profiles.store
    ]
