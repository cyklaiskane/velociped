from databases import DatabaseURL
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret

config = Config(".env")

POSTGRES_DSN = config("POSTGRES_DSN", cast=DatabaseURL)

CORS_ORIGINS = config("CORS_ORIGINS", cast=CommaSeparatedStrings, default="*")

LM_CLIENT_ID = config("LM_CLIENT_ID", cast=Secret)
LM_CLIENT_SECRET = config("LM_CLIENT_SECRET", cast=Secret)
LM_TOKEN_URL = config("LM_TOKEN_URL")
