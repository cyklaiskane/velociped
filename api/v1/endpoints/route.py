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
async def route(
    query: RouteQuery,
    request: Request,
    output: str = 'routes',
) -> Union[List, JSONResponse]:
    routes = []

    logging.debug(query)
    use_profiles = []
    if query.profile_name is None:
        use_profiles = profiles.store
    elif isinstance(query.profile_name, str):
        use_profiles = [profiles.get(query.profile_name, False)]
    else:
        use_profiles = [
            profiles.get(profile_name, False) for profile_name in query.profile_name
        ]
    if not use_profiles:
        return JSONResponse(content={'error': 'No profiles found'}, status_code=500)

    try:
        results = await asyncio.gather(
            *[do_route(query.waypoints, profile) for profile in use_profiles]
        )
    except Exception as e:
        logging.warn(e)
        return JSONResponse(content={'error': str(e)}, status_code=500)
    for route in results:
        routes.append(route)
    if output == 'routes':
        return routes
    elif output == 'geojson':
        return routes[0].geojson


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
    return [
        profile.dict(include={'name', 'label', 'description'})
        for profile in profiles.store
    ]
