import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware

from api import v1
from api.config import (
    CORS_ORIGINS,
    HOST,
    LM_ADDRESS_BASE_URL,
    LM_CLIENT_ID,
    LM_CLIENT_SECRET,
    LM_TOKEN_URL,
    PORT,
)
from api.database import db
from api.security import oauth

app = FastAPI()

logging.getLogger('databases').setLevel(logging.INFO)

app.mount('/assets', StaticFiles(directory='assets'), name='assets')

origins = []
for origin in CORS_ORIGINS:
    use_origin = origin.strip()
    origins.append(use_origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(v1.router, prefix='/v1')

templates = Jinja2Templates(directory='templates')


@app.get('/')
async def index(request: Request) -> Any:
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/ping')
async def ping() -> str:
    return 'ok'


@app.on_event('startup')
async def startup() -> None:
    await db.connect()

    oauth.register(
        'lm',
        client_id=str(LM_CLIENT_ID),
        client_secret=str(LM_CLIENT_SECRET),
        access_token_url=LM_TOKEN_URL,
        client_kwargs={
            'grant_type': 'client_credentials',
            'headers': {'Accept': 'application/json',},
        },
        api_base_url=LM_ADDRESS_BASE_URL,
    )


@app.on_event('shutdown')
async def shutdown() -> None:
    await db.disconnect()


def main() -> None:
    import uvicorn

    uvicorn.run('api.main:app', host=HOST, port=PORT, reload=True, log_level='debug')


if __name__ == '__main__':
    main()
