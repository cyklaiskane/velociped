from typing import List, Optional, Tuple, Literal, Dict, Any
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel
from pydantic.dataclasses import dataclass


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


class Adressplatsbeteckning(BaseModel):
    adressplatsnummer: Optional[str]
    bokstavstillagg: Optional[str]
    lagestillag: Optional[Literal['UH', 'UV', 'U']]
    lagestillaggsnummer: Optional[int]
    avvikandeAdressplatsbeteckning: Optional[str]
    avvikerFranStandarden: bool


class Punkt(BaseModel):
    type: Literal['Point']
    coordinates: List[int]


class AdressplatsAttribut(BaseModel):
    adressplatsbeteckning: Adressplatsbeteckning
    adressplatstyp: Literal['Gatuadressplats', 'Metertalsadressplats', 'Byadressplats', 'Gårdsadressplats']
    insamlingslage: Literal['Byggnad', 'Ingång', 'Infart', 'Tomtplats', 'Ungefärligt lägesbestämd', 'Övrigt läge']
    adressplatspunkt: Punkt
    statusForBelagenhetsadress: Literal['Reserverad', 'Gällande']
    postnummer: Optional[int]
    postort: Optional[str]


class AdressplatsNamn(BaseModel):
    popularnamn: str
    ortid: Optional[str]


class Kommun(BaseModel):
    kommunkod: str
    kommunnamn: str


class Kommundel(BaseModel):
    objektidentitet: UUID
    objektversion: int
    versionGiltigFran: Optional[datetime]
    faststalltNamn: str
    ortid: Optional[str]
    objektstatus: Literal['Planerad', 'Gällande under utredning', 'Gällande', 'Avregistrerad']
    kommun: Kommun


class BaseAdressOmrade(BaseModel):
    objektidentitet: UUID
    objektversion: int
    versionGiltigFran: Optional[datetime]
    faststalltNamn: str
    ortid: Optional[str]
    adressomradestyp: Literal['Gatuadressområde', 'Metertalsadressområde', 'Byadressområde']
    objektstatus: Literal['Planerad', 'Gällande under utredning', 'Gällande', 'Avregistrerad']


class AdressOmrade(BaseAdressOmrade):
    kommundel: Kommundel


class GardsAdressOmrade(BaseAdressOmrade):
    adressomrade: AdressOmrade


class AdressplatsAnmarkning(BaseModel):
    anmarkningstyp: str
    anmarkningstext: str


class AdressattAnlaggning(BaseModel):
    anlaggningstyp: str
    anlaggningstext: Optional[str]


class Registerenhetsreferens(BaseModel):
    objektidentitet: UUID


class Distrikttillhorighet(BaseModel):
    distriktskod: str
    distriktsnamn: str


class Adress(BaseModel):
    objektidentitet: UUID
    objektversion: int
    versionGiltigFran: Optional[datetime]
    objektstatus: Literal['Planerad', 'Gällande under utredning', 'Gällande', 'Avregistrerad']
    adressplatsattribut: Optional[AdressplatsAttribut]
    adressplatsnamn: Optional[AdressplatsNamn]
    adressomrade: Optional[AdressOmrade]
    gardsadress: Optional[GardsAdressOmrade]
    adressplatsanmarkning: Optional[List[AdressplatsAnmarkning]]
    adressattanlaggning: Optional[AdressattAnlaggning]
    registerenhetsreferens: Optional[List[Registerenhetsreferens]]
    distrikttillhorighet: Optional[Distrikttillhorighet]

    @property
    def display_name(self) -> str:
        house = None
        street = None
        place = None
        muni = None

        if self.adressplatsattribut and self.adressplatsattribut.adressplatsbeteckning:
            if self.adressplatsattribut.adressplatsbeteckning.adressplatsnummer:
                house = self.adressplatsattribut.adressplatsbeteckning.adressplatsnummer
            elif self.adressplatsattribut.adressplatsbeteckning.avvikandeAdressplatsbeteckning:
                house = self.adressplatsattribut.adressplatsbeteckning.avvikandeAdressplatsbeteckning

        if self.adressomrade and self.adressomrade.faststalltNamn:
            street = self.adressomrade.faststalltNamn
        elif self.adressplatsnamn and self.adressplatsnamn.popularnamn:
            street = self.adressplatsnamn.popularnamn

        if self.adressomrade and self.adressomrade.kommundel:
            if self.adressomrade.kommundel.faststalltNamn:
                place = self.adressomrade.kommundel.faststalltNamn
            if self.adressomrade.kommundel.kommun:
                muni = self.adressomrade.kommundel.kommun.kommunnamn

        part1 = ' '.join([v for v in [street, house] if v is not None])
        name = ', '.join([v for v in [part1, place, muni] if v is not None])

        return name


class AdressFeature(BaseModel):
    type: Literal['Feature']
    id: UUID
    bbox: List[float]
    geometry: Any
    properties: Adress

    @property
    def display_name(self) -> str:
        return self.properties.display_name


class AdressResponse(BaseModel):
    type: Literal['FeatureCollection']
    crs: Dict
    bbox: List[float]
    features: List[AdressFeature]


class AdressReferens(BaseModel):
    objektidentitet: UUID
    beteckning: str


@dataclass
class AdressReferensResponse:
    refs: List[AdressReferens]
