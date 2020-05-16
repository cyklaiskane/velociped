import logging
from typing import Optional

from devtools import debug
from fastapi import Request
from pydantic import BaseModel


class OAuth2Token(BaseModel):
    name: str
    token_type: str = None
    access_token: str = None
    refresh_token: Optional[str]
    expires_at: int = None


tokens = []


async def fetch_token(name: str, request: Request):
    logging.debug("fetch_token")
    logging.debug(name)
    debug(tokens)
    for token in tokens:
        if token.name == name:
            return token.dict(exclude={"name"})
    token = OAuth2Token(
        name=name, token_type="Bearer", access_token="cafe", expires_at=1
    ).dict(exclude={"name"})
    debug(token)
    return token


async def update_token(
    name, token, refresh_token=None, access_token=None, expires_at=None
):
    debug(name, token, refresh_token, access_token)
    for i, _token in enumerate(tokens):
        if _token.name == name and _token.access_token == access_token:
            tokens[i] = OAuth2Token(**token)
            return
    tokens.append(OAuth2Token(name=name, **token))
    debug(tokens)
