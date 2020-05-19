import logging
from typing import List, Optional

from authlib.oauth2.auth import OAuth2Token
from devtools import debug
from fastapi import Request

from api.schemas import Token

tokens: List[Token] = []


async def fetch_token(name: str, request: Request) -> dict:
    logging.debug('fetch_token')
    logging.debug(name)
    debug(tokens)
    for token in tokens:
        if token.name == name:
            return token.dict(exclude={'name'})
    token = Token(name=name, token_type='Bearer', access_token='cafe', expires_at=1)
    debug(token)
    return token.dict(exclude={'name'})


async def update_token(
    name: str,
    token: OAuth2Token,
    refresh_token: Optional[str] = None,
    access_token: Optional[str] = None,
    expires_at: Optional[int] = None,
) -> None:
    debug(name, token, refresh_token, access_token)
    for i, _token in enumerate(tokens):
        if _token.name == name and _token.access_token == access_token:
            tokens[i] = OAuth2Token(**token)
            return
    tokens.append(Token(name=name, **token))
    debug(tokens)
