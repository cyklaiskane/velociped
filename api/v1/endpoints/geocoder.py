from typing import Dict, List

from fastapi import APIRouter, Request
from pyproj import Transformer

from api.schemas import AdressFeature, AdressReferensResponse, AdressResponse
from api.security import oauth

router = APIRouter()


def parse_result(feature: AdressFeature) -> dict:
    to4326 = Transformer.from_crs('epsg:3006', 'epsg:4326', always_xy=True)

    name = feature.display_name
    coords = feature.properties.adressplatsattribut.adressplatspunkt.coordinates  # type: ignore
    loc = to4326.transform(*coords)

    return {
        'name': name,
        'lat': loc[1],
        'lng': loc[0],
        'feature': feature,
    }


@router.get('/search/{text}')
async def address_search(text: str, request: Request) -> List:
    r = await oauth.lm.get(
        f'referens/fritext/{text}', params={'maxHits': 5}, request=request
    )
    r.raise_for_status()
    refs = AdressReferensResponse(r.json()).refs
    ids = [ref.objektidentitet for ref in refs]
    r = await oauth.lm.post(
        '', json=ids, params={'includeData': 'basinformation'}, request=request
    )
    r.raise_for_status()
    result = AdressResponse(**r.json())
    response = [parse_result(feature) for feature in result.features]
    return response


@router.get('/reverse/{lat},{lng}')
async def reverse(lat: float, lng: float, request: Request) -> Dict:
    to3006 = Transformer.from_crs('epsg:4326', 'epsg:3006', always_xy=True)
    e, n = to3006.transform(lng, lat)
    r = await oauth.lm.get(
        f'punkt/3006/{n},{e}', params={'includeData': 'basinformation'}, request=request
    )
    r.raise_for_status()
    result = AdressResponse(**r.json())
    feature = result.features[0]
    response = parse_result(feature)
    return response
