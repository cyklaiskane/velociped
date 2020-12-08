# Velociped

## Introduktion

Velociped är ett kombinerat ruttnings-API och webbgränssnitt utvecklat för [cyklaiskane.se](https://www.cyklaiskane.se). API-delen är byggd i Python 3 med FastAPI som ramverk och använder PostgreSQL med PostGIS/pgRouting tillägg för ruttberäkning och MVT-generering.

Webbgränssnittet är byggt i ES6 Javascript och använder Leaflet som kartramverk med Leaflet Routing Machine insticksmodul som ruttningsgränssnitt.


## Använding

API:t erbjuder tre tjänster som kan anropas via HTTP: _/route_, _/tiles_, och _/tiles_.

### /route

För att göra ett ruttuppslag kan man skicka en _POST_ förfrågan till `/route` med ett JSON-objekt bestående av ett antal målpunkter och eventuellt namnet på en ruttprofil genom att inkludera attributen `profile_name` i objektet. Exempel på JSON-objekt:

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

## Utveckling

Följande mjukvara krävs för utveckling

- Docker
- Node.js 12+
- Python 3.8+
  - Poetry

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
docker-compose -f docker-compose.yml -f docker-compose-dev.yml up
```

### UI

```shell
npm run serve
```

## Konfiguration

Följande miljövariabler kan sättas (standardvärde inom parentes)

BIND_HOST
: Vilken IP-adress API ska lyssna på (0.0.0.0)

BIND_PORT
: Vilken TCP port API ska lyssna på (8000)

CORS_ORIGINS
: Kommaseparerad lista över tillåtna CORS-värdnamn (\*)

POSTGRES_DSN
: Sökväg till en PostgreSQL databas i formen _postgres://användarnamn:lösenord@adress:port/databas_

TILES_BG_URL
: Leaflet-kompatibel Tile URL för bakgrundskarta. Ex _https://maps.example.com/{z}/{x}/{y}.png

TILES_TS_URL
: Leaflet-kompatibel Tile URL för trafiksäkerhetsklassat nätverk

GEODATA_URL
: Sökväg till källa för kartdata. Kan antingen vara en GeoPackage-fil eller en WFS adress. Om det är en WFS-adress ska URL-strängen börja med `wfs:`. Ex `wfs:https://geoserver.example.com/wfs`.

GEODATA_LAYER
: Lagernamn för kartdata

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

API stödjer även att läsa miljövariabler från en _.env_ fil.

## Driftsättning

...
