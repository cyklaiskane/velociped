from fastapi import APIRouter

from api.v1.endpoints import geocoder, route, tiles

router = APIRouter()
router.include_router(geocoder.router, prefix='/geocoder', tags=['geocoder'])
router.include_router(route.router, prefix='/route', tags=['route'])
router.include_router(tiles.router, prefix='/tiles', tags=['tiles'])
