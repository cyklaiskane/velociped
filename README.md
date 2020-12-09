# Velociped

## Introduktion

Velociped är ett kombinerat ruttnings-API och webbgränssnitt utvecklat för [cyklaiskane.se](https://www.cyklaiskane.se). API-delen är byggd i Python 3 med FastAPI som ramverk och använder PostgreSQL med PostGIS/pgRouting tillägg för ruttberäkning och MVT-generering.

Webbgränssnittet är byggt i ES6 Javascript och använder Leaflet som kartramverk med Leaflet Routing Machine insticksmodul som ruttningsgränssnitt.

## Snabbstart

Kräver _git_ och _Docker_. Klona projektet med `git clone https://github.com/cyklaiskane/velociped.git` byt katalog till `velociped`. Skapa en konfigurations-texfil i enlighet med avsnittet [konfiguration](#konfiguration) och sätt eventuellt värden för _TILES_BG_URL_ och _LM..._. Övriga värden är hårdkodade i _docker-compose.yml_.

Kör sedan

```shell
docker-compose build
```

behöver bara göras första gången eller om källkoden uppdaterats. Det går nu att starta en instans med

```shell
docker-compose up
```

## Använding

API:t erbjuder tre tjänster som kan anropas via HTTP: _/v1/route_, _/v1/tiles_, och _/v1/geocoder_.

### /route

För att göra ett ruttuppslag kan man skicka en _POST_ förfrågan till `/v1/route` med ett JSON-objekt bestående av ett antal målpunkter och eventuellt namnet på en ruttprofil genom att inkludera attributen `profile_name` i objektet. Exempel på JSON-objekt:

```json
{
  "waypoints": [
    {
      "lat": 0.0,
      "lng": 0.0
    },
    {
      "lat": 0.7,
      "lng": 0.4
    }
  ]
}
```

och med profil-definition

```json
{
  "waypoints": [
    {
      "lat": 0.0,
      "lng": 0.0
    },
    {
      "lat": 0.7,
      "lng": 0.4
    }
  ],
  "profile_name": "fastest"
}
```

Man kan testa anrop med hjälp av t.ex. [Postman](https://www.postman.com/) eller [curl](https://curl.se/) (curl -d @test.json http://example.com/v1/route).

Svaret returneras som ett JSON objekt med följande struktur:

```json
{
  "name": "Ruttnamn",
  "length": 42.0,
  "duration": 2100,
  "segments": [
    {
      "coords": [[0, 0], [0.2, 0.35], [0.4, 0.7]],
      "danger_coords": [],
      "name": "Vägnamn",
      "ts_klass": "C1",
      "length": 42.0,
      "duration": 2100
    }
  ]
}
```

Det går även att ange parametern `output=geojson` i URLen (ex `http://example.com/v1/route?output=geojson`) när en förfrågan görs för att få resultatet som en samling GeoJSON-objekt.

Profiler defineras genom att skapa en JSON-fil med namnet `profiles.json` som placeras i projekt-katalogen. Innehållet bör ha följande utseende:

```json
[
  {
    "name": "suggested",
    "label": "Föreslagen väg",
    "description": "",
    "speeds": {
      "C1": 18,
      "C2": 15,
      "C3": 18,
      "B1": 18,
      "B2": 18,
      "B3": 18,
      "B4": 18,
      "B5":  1,
      "G1": 15,
      "G2": 13
    },
    "weights": {
      "C1":  1.0,
      "C2":  1.1,
      "C3":  1.1,
      "B1":  1.2,
      "B2":  1.3,
      "B3":  1.5,
      "B4":  2.1,
      "B5": -1,
      "G1":  1.4,
      "G2":  1.6
    }
  }
]
```

Attributen _name_ bör endast bestå av bokstäver utan accenter. Attributobjektet _speeds_ definerar hastigheten i km/t för varje TS-klass och _weights_ anger en vikt, där högre värde på betyder farligare väg.


### /tiles

Det trafiksäkerhetsklassade vägnätet som ligger som grund för ruttmotorn kan hämtas som tiles i [MVT](https://docs.mapbox.com/vector-tiles/specification/)-format. Följer samma XYZ numreringsschema som Google Maps/OpenStreetMap.

```
http://example.com/v1/tiles/ts/<z>/<x>/<y>.pbf
```


### /geocoder

Geocodern fungerar enbart som ett ombud för Lantmteriets adresstjänst. För att göra adressökning görs en _GET_ förfrågan mot `/v1/geocoder/search/<fritext>`. Svaret är en samling JSON-objekt med adresser och koordinater. Ex:

```json
[
  {
    "name": "Null Island 1",
    "lat": 0,
    "lng": 0,
    "feature": {}
  }
]
```

Det går även att göra omvänd geokodning genom att skicka en _GET_ förfrågan till `/v1/geocoder/reverse/<lat>,<lng>` med EPSG:4326 koordinater. Svaret är ett JSON-objekt med samma struktur som vid adressökning.

## Utveckling

Följande mjukvara krävs för utveckling

- [git](https://git-scm.com/)
- [Docker](https://www.docker.com/)
- [Node.js 12+](https://nodejs.org/)
- [Python 3.8+](https://www.python.org/)
  - [Poetry](https://python-poetry.org/)


Klona källkoden genom att köra

```shell
git clone https://github.com/cyklaiskane/velociped
```


### API

Källkoden för ruttningsmotorn hittas i katalogen _api/_. API-koden använder [Poetry](https://python-poetry.org) för pakethantering. För att installera beroenden kör:

```shell
poetry install --no-root
```

Detta skapar en virtuell miljö med alla externa bibliotek som behövs.


### UI

Källkoden hittas i katalogen _src/_. För att installera nödvändiga paket, kör:

```shell
npm install
```


## Köra


### API

En ensam API-instans kan startas med `poetry run serve`.

En komplett miljö kan startas med:

```shell
docker-compose up
```

Eventuellt behöver Docker-avbilder byggas först innan miljön startas upp. Detta kan göras med nedanstående kommando.

```shell
docker-compose build
```

Se nedan för hur miljön ska konfigureras.


### UI

För att starta en utvecklingsversion av webbgränssnittet kör:

```shell
npm run serve
```

För att bygga en statisk distribuerbar version:

```shell
npm run build
```

## Konfiguration

Följande miljövariabler kan sättas (standardvärde inom parentes)

API_BASE_URL
: Basadress till API. Används av UI-delen för att veta vart ruttförfrågningar ska skickas.

BIND_HOST
: Vilken IP-adress API ska lyssna på (0.0.0.0)

BIND_PORT
: Vilken TCP port API ska lyssna på (8000)

CORS_ORIGINS
: Kommaseparerad lista över tillåtna CORS-värdnamn (\*)

POSTGRES_DSN
: Sökväg till en PostgreSQL databas i formen _postgres://användarnamn:lösenord@adress:port/databas_

TILES_BG_URL
: Leaflet-kompatibel Tile URL för bakgrundskarta med samma schema som Google Maps/OpenStreetMap. Ex _https://maps.example.com/{z}/{x}/{y}.png

TILES_TS_URL
: Leaflet-kompatibel Tile URL för trafiksäkerhetsklassat nätverk

GEODATA_URL
: Sökväg till källa för kartdata. Kan antingen vara en GeoPackage-fil eller en WFS adress. Om det är en WFS-adress ska URL-strängen börja med `wfs:`. Ex `wfs:https://geoserver.example.com/wfs`.

GEODATA_LAYER
: Lagernamn för kartdata i EPSG:3006

GEODATA_BBOX
: Eventuell begränsning av området som ska importeras i formatet _xmin,ymin,xmax,ymax_ med EPSG:3006 koordinater.

GEODATA_UPDATE_INIT
: Anger om geodatan ska uppdateras direkt när tjänsten startar. `True` eller `False` (False)

GEODATA_UPDATE_INTERVAL
: Anger hur ofta geodatan ska uppdateras; integervärde i sekunder. 0 anger att ingen periodisk uppdatering ska genomföras.

LM_CLIENT_ID
: Klient-ID för Lantmäteriets API

LM_CLIENT_SECRET
: Nyckel för Lantmäteriets API

LM_TOKEN_URL
: URL för Lantmäteriets OAuth2 token tjänst (https://api.lantmateriet.se/token)

LM_ADDRESS_BASE_URL
: Bas-URL för Lantmäteriets adresstjänst. (https://api.lantmateriet.se/distribution/produkter/belagenhetsadress/v4.1/)

API stödjer även att läsa miljövariabler från en _.env_ fil. Skapa en textfil som heter `.env` i projektkatalogen och skriv in en miljövariabel med efterföljande likamedtecken och sedan värdet för variabeln på var rad. T.ex.:

```shell
GEODATA_URL=wfs:http://exempel/service
GEODATA_LAYER=tsnet
GEODATA_UPDATE=True
```

## Driftsättning

...
