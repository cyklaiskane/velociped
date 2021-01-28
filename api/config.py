from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

config = Config('.env')

ENV = config('ENV', default='prod')
LOG_LEVEL = config('LOG_LEVEL', default='info')

HOST = config('BIND_HOST', default='0.0.0.0')
PORT = config('BIND_PORT', cast=int, default=8000)

TILES_BG_URL = config(
    'TILES_BG_URL', default='http://localhost:3000/styles/bg/{z}/{x}/{y}.png'
)
TILES_TS_URL = config(
    'TILES_TS_URL', default='http://localhost:3000/styles/velo/{z}/{x}/{y}.png'
)

POSTGRES_DSN = config('POSTGRES_DSN', cast=DatabaseURL)

GEODATA_URL = config('GEODATA_URL')
GEODATA_LAYER = config('GEODATA_LAYER')
GEODATA_BBOX = config('GEODATA_BBOX', cast=CommaSeparatedStrings, default=None)

GEODATA_UPDATE_INIT = config('GEODATA_UPDATE_INIT', cast=bool, default=False)
GEODATA_UPDATE_INTERVAL = config('GEODATA_UPDATE_INTERVAL', cast=int, default=0)

GEODATA_TABLE = 'cyklaiskane'

CORS_ORIGINS = config('CORS_ORIGINS', cast=CommaSeparatedStrings, default='*')

LM_CLIENT_ID = config('LM_CLIENT_ID', cast=Secret)
LM_CLIENT_SECRET = config('LM_CLIENT_SECRET', cast=Secret)
LM_TOKEN_URL = config('LM_TOKEN_URL', default='https://api.lantmateriet.se/token')
LM_ADDRESS_BASE_URL = config(
    'LM_ADDRESS_BASE_URL',
    default='https://api.lantmateriet.se/distribution/produkter/belagenhetsadress/v4.1/',
)
