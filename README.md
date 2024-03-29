# Velociped

## Introduktion

Velociped är ett kombinerat HTTP ruttnings-API och webbgränssnitt utvecklat för [cyklaiskane.se](https://www.cyklaiskane.se). API-delen är byggd i Python 3 med [FastAPI](https://fastapi.tiangolo.com/) som ramverk och använder PostgreSQL med PostGIS/pgRouting tillägg för ruttberäkning och MVT-generering.

Webbgränssnittet är byggt i ES6 Javascript och använder [Leaflet](https://leafletjs.com/) som kartramverk med [Leaflet Routing Machine](https://www.liedman.net/leaflet-routing-machine/) insticksmodul som ruttningsgränssnitt.


## Vägnätsdata

Geodata som används som vägnät är NVDB-data som har trafiksäkerhetsklassats av ett [FME-skript](https://github.com/Region-Skane/nvdb-tools/tree/master/classify) utvecklat av Region Skåne. Datan som används är i SWEREF99TM/EPSG:3006 koordinatsystem och bör inehålla följande attribut:


attributnamn                  datatyp
------------------------      ----------
objectid                      heltal
ts_klass                      textsträng
namn_130                      textsträng
klass_181                     heltal
konst_190                     textsträng
f_forbjuden_fardriktning      heltal
b_forbjuden_fardriktning      heltal
shape_length                  flyttal
from_vertex                   heltal
to_vertex                     heltal


## Snabbstart

Kräver _git_ och _Docker_. Klona projektet med

```shell
git clone https://github.com/cyklaiskane/velociped.git
```

Byt därefter katalog till `velociped`. Skapa en konfigurations-textfil i enlighet med avsnittet [konfiguration](#konfiguration) och sätt eventuellt värden för _TILES_BG_URL_ och _LM..._. Övriga värden är hårdkodade i _docker-compose.yml_.

Kör sedan

```shell
docker-compose build
```

Detta behöver bara göras första gången eller om källkoden uppdaterats. Det går nu att starta en instans med

```shell
docker-compose up
```

När instansen förberett databasen och uppdaterat den med geodata så finns den tillgänglig på http://localhost:8080.


## Använding

API:t erbjuder tre tjänster som kan anropas via HTTP: _/v1/route_, _/v1/tiles_, och _/v1/geocoder_. Det finns även en automatiskt genererad API-dokumentation tillgänglig på _/docs_. Alla sökvägar är relativt till adressen där APIt har startats. T.ex. kan den automatiska dokumentationen nås via http://localhost:8080/docs om man följer instruktionerna i [snabbstart](#snabbstart).


### /route

För att göra en ruttsökning kan man skicka en _POST_ förfrågan till `/v1/route` med ett ruttförfrågnings JSON-objekt bestående av ett antal WGS84/EPSG:4326 koordinater samt namnet på en ruttprofil. Exempel på JSON-objekt:

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

Attributen _waypoints_ är en lista med objekt med attributen _lat_ och _lng_ som är WGS84/EPSG:4326 koordinater. Minst två koordinat-objekt måste inkluderas för att en ruttsökning kan göras. Attributen _profile_name_ anger vilken profil som ska användas för rutsökning.

Det går även att lämna bort _profile_name_. Då används den första [profilen som definerats](#profiler).

Man kan testa anrop med hjälp av t.ex. [Postman](https://www.postman.com/) eller [curl](https://curl.se/). Exempel med _curl_ om man först skapar en JSON-fil med namnet _test.json_ som innehåller ett ruttförfrågningsobjekt:

```shell
curl -d @test.json http://localhost:8080/v1/route
```

Svaret returneras som ett JSON-objekt med följande struktur:

```json
{
  "name": "Profil",
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

Där _name_ är det beskrivande namnet på den ruttprofil som använts, _length_ är totala längden på rutten i meter, _duration_ beräknad tid att fördas hela sträckan i sekunder. Attributen _segments_ är en lista med segment-objekt i den ordning de ska besökas.

Segment-objekten har följande attribut:

coords
: en lista WGS84/EPSG:4326 koordinater med ordningen \[_longitud_, _latitud_\].

danger_coords
: WGS84/EPSG:4326 koordinater där rutten korsar en farlig väg

name
: namnet på vägsegmentet eller _null_ om namn saknas

ts_klass
: den trafiksäkerhetsklassning som Region Skånes [FME-skript](https://github.com/Region-Skane/nvdb-tools/tree/master/classify) har beräknat

length
: längden på segmentet i meter

duration
: beräknad tid för segmentet i sekunder

Det går även att ange parametern _output_ med värdet _geojson_ i URLen (t.ex. _http://&shy;example.com&shy;/v1/route&shy;?output=geojson_) när en förfrågan görs för att få resultatet som en samling GeoJSON FeatureCollection-objekt. Attributen hittas då i _properties_ för varje feature.


### /tiles

Det trafiksäkerhetsklassade vägnätet som ligger som grund för ruttmotorn kan hämtas som tiles i [MVT](https://docs.mapbox.com/vector-tiles/specification/)-format. Följer samma [XYZ numreringsschema](https://en.wikipedia.org/wiki/Tiled_web_map#Tile_numbering_schemes) som Google Maps/OpenStreetMap.

```
http://example.com/v1/tiles/ts/<z>/<x>/<y>.pbf
```

Ersätt `example.com` med adressen till API-instansen.

### /geocoder

Geocodern fungerar enbart som ett ombud för Lantmäteriets [adresstjänst](https://www.lantmateriet.se/globalassets/kartor-och-geografisk-information/geodatatjanster/belagenhetsadress_v4.1-tekniskbeskrivning.pdf). För att göra adressökning görs en _GET_ förfrågan mot `/v1/geocoder/search/<fritext>`. Där _fritext_ skickas direkt vidare till _/referens/fritext/<fritext>_ hos [Lantmäteriets API]((https://www.lantmateriet.se/globalassets/kartor-och-geografisk-information/geodatatjanster/belagenhetsadress_v4.1-tekniskbeskrivning.pdf)) och lyder under samma restriktioner. Svaret är en samling JSON-objekt med adresser och koordinater. Ex:

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

Där _name_ är namnet på den adress som hittats, _lat_ och _lng_ är WGS84/EPSG:4326 koordinater för adressen och _feature_ är hela det GeoJSON Feature-objekt som returneras av Lantmäteriets API i ett _BelagenhetsadressResponse_.

Det går även att göra omvänd geokodning genom att skicka en _GET_ förfrågan till `/v1/geocoder/reverse/<lat>,<lng>` med WGS84/EPSG:4326 koordinater. Svaret är ett JSON-objekt med samma struktur som vid adressökning.

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

### Variabler

Följande miljövariabler kan sättas (standardvärde inom parentes)

API_BASE_URL
: Basadress till API. Används av UI-delen för att veta vart ruttförfrågningar ska skickas. Lämnas tomt när UI-delen körs direkt från API-tjänsten.

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

### Profiler

Profiler defineras genom att skapa en JSON-fil med namnet `profiles.json` som placeras i projekt-katalogen. Innehållet är en lista med objekt som beskriver olika ruttningsprofiler. Exempel på innehåll:

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

Profilobjektet ska ha enbart följande attribut: _name_ bör endast bestå av bokstäver utan accenter och fungerar som identitet för profilen vid ruttuppslag, _label_ är ett mer beskrivande namn på profilen och visas i webgränssnittet, _description_ kan användas för att mer utförligt beskriva profilen. Attributobjektet _speeds_ definerar hastigheten i km/t för varje TS-klass och _weights_ anger en godtycklig vikt, där högre värde på betyder farligare väg. En negativ vikt anger att sträckor med den klassen ska undantas vid ruttsökning.

TS-klasserna är följande

namn  beskrivning
----  -------------------
C1    Cykelväg
C2    Cykelväg på grus
C3    Cykelfält
B1    Lågtrafikerad väg
B2    Lättrafikerad väg
B3    Medeltrafikerad väg
B4    Högtrafikerad väg
B5    Väg med cykelförbud
G1    Bra grusväg
G2    Grusväg


För att ändra/lägga till/ta bort TS-klasser är det följande filer som berörs:

```
src/ts-styles.js
api/schemas.py
profiles.json
```

Ska man ändra vilken/vilka attribut som används för ruttberäkning behöver man bekanta sig med hela kodbasen och då främst med `api/v1/utils/route.py`.


### Lager

Kartlager definers i en fil med namnet `layers.json` i bas-katalogen. Formatet för filen är följande:

```json
{
  "backgrounds": [
    {
      "type": "tms" eller "tiles" eller "wms",
      "url": "https://example.com/standard/leaflet/layer/url/{z}/{x}/{y}.png",
      "name": "Namn på lagret",
      "description": "Beskrivning av lagret. T.ex. symboler och annat. Kan innehålla <b>HTML</b>",
      "options": {
        "attribution": "Standard Leaflet lager 'options'"
      }
    }
  ],
  "overlays": [
    {}
  ]
}
```

Rotobjektet innehåller bör innehålla attributen `backgrounds` och `overlays` som är listor med lagerdefinitioner. Den förstnämnda anger bakgrundkartor och den senare överliggande lager. Varje lagerdefinition är ett objekt som måste innehålla attributen `type`, `url`, och `name`. Lagerdefinitionen kan även ha attributen `description` som tillåter en mer utförlig beskrivning av lagerinnehållet och kan innehålla HTML. Attributen `options` är ett objekt som direkt skickas vidare till Leaflet-lagret som skapas och kan innehålla de parametrar som beskrivs i Leafelts (dokumentation)[https://leafletjs.com/reference-1.7.1.html#tilelayer].

## Enkel driftsättning

Tjänsten är utvecklad för att köras i Region Skånes Azure-miljö på en virtuell maskin som kör Debian 11 eller senare. För att förbereda maskinen och starta tjänsten följer nedan en samling kommandon.


### Förberedelser

Nedanstående kommandon bör köras för att installera och konfigurera en maskin så att tjänsten kan startas. Det förutsätter att  man är inloggad på maskinen som användaren _azureuser_ och har "sudo" rättigheter.


```shell
# Install required dependencies to install Docker CE
sudo apt install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common

# Add Docker package signing keys
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -

# Add Docker CE repository
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/debian \
   $(lsb_release -cs) \
   stable"

# Refresh pckage db and install
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io

# Fetch docker-composer and make it executable. Note: bump version number
sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -a -G docker azureuser

# Install project build prerequisites
sudo apt install make git
# Clone project source
git clone https://github.com/cyklaiskane/velociped.git
# Change to project directory
cd velociped
```

I det här skedet är all programvara och källkod på plats för att bygga och starta tjänsten. Det som nu krävs är att skapa en fil med namnet `.env` för att sätta värden på en del konfigurationsvariabler. Innehållet kan se ut som nedan.

```shell
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<you password here>
POSTGRES_DB=postgres
POSTGRES_HOST=db

#GEODATA_URL=wfs:http://geodata.skane.se:8080/geoserver/wfs
#GEODATA_LAYER=rs:cyklaiskane_trafiksakerhetsklassat_natverk

# Required for geocoding
LM_TOKEN_URL=https://api.lantmateriet.se/token
LM_CLIENT_ID=<provided id here>
LM_CLIENT_SECRET=<provided secret here>

# Uncomment to override default
#TILES_TS_URL=https://maps.cyklaiskane.se/trafiksakerhet/{z}/{x}/{y}.png
#TILES_BG_URL=https://maps.cyklaiskane.se/nedtonad/{z}/{x}/{y}.png

# Address to api and maps/tiles endpoint. Uncomment to override default
#API_ADDRESS=api.cyklaiskane.se
#MAPS_ADDRESS=maps.cyklaiskane.se
```

Allt är nu på plats för att bygga docker-avbilder och starta tjänsten.

```shell
# Build all docker images
make
# Start service and all dependecy services
docker-compose up -d
```


### Uppdatera tjänsten

För att uppdatera tjänsten med nyare källkod eller vid ändring av konfigurationsvariabler kan man köra nedanstående kommandon i källkodskatalogen (_velociped_ om man följt tidigare instruktioner).

```shell
# Fetch latest version of project source
git fetch
# Apply changes to local files
git rebase
# Build images
make
# Start
docker-compose up -d
```
