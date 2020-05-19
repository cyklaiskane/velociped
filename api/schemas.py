from typing import List, Optional, Tuple

from pydantic import BaseModel


class LatLng(BaseModel):
    lat: float
    lng: float

    def to_xy(self) -> List[float]:
        return [self.lng, self.lat]


class RouteQuery(BaseModel):
    waypoints: List[LatLng]


class Segment(BaseModel):
    coords: List[Tuple[float, float]]
    name: Optional[str]
    ts_klass: str
    length: float
    duration: float


class Route(BaseModel):
    name: str = ''
    length: float = 0.0
    duration: float = 0.0
    segments: List[Segment] = []


class Token(BaseModel):
    name: str
    token_type: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_at: Optional[int]
