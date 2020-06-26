from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

config = Config('.env')

HOST = config('BIND_HOST', default='0.0.0.0')
PORT = config('BIND_PORT', cast=int, default=8000)

TILES_BG_URL = config('TILES_BG_URL', default='http://localhost:3000/styles/bg/{z}/{x}/{y}.png')
TILES_TS_URL = config('TILES_TS_URL', default='http://localhost:3000/styles/velo/{z}/{x}/{y}.png')

POSTGRES_DSN = config('POSTGRES_DSN', cast=DatabaseURL)

CORS_ORIGINS = config('CORS_ORIGINS', cast=CommaSeparatedStrings, default='*')

LM_CLIENT_ID = config('LM_CLIENT_ID', cast=Secret)
LM_CLIENT_SECRET = config('LM_CLIENT_SECRET', cast=Secret)
LM_TOKEN_URL = config('LM_TOKEN_URL', default='https://api.lantmateriet.se/token')
LM_ADDRESS_BASE_URL = config(
    'LM_ADDRESS_BASE_URL',
    default='https://api.lantmateriet.se/distribution/produkter/belagenhetsadress/v4.1/',
)
