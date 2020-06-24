#
# UI builder
#
FROM node:lts-alpine as node-builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . ./

ENV NODE_ENV=production \
    APP_API_URI=''

RUN npm run build

#
# Base
#
FROM python:3.8-alpine as base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1

WORKDIR /app

#
# API builder
#
FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache build-base libressl-dev libffi-dev gcc musl-dev \
      python3-dev libxml2-dev libxslt-dev postgresql-dev geos-dev proj-dev proj-util

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

ARG BUILD_ENV=dev

RUN set -euxo pipefail; \
    python -m venv /venv; \
    POETRY_ARGS=""; \
    [ "${BUILD_ENV}" = "dev" ] && POETRY_ARGS="--dev"; \
    poetry export $POETRY_ARGS -f requirements.txt \
      | /venv/bin/pip install -r /dev/stdin


#
# Final
#
FROM base as final

RUN apk add --no-cache libffi libpq geos proj-util

COPY --from=builder /venv /venv
COPY . ./
COPY --from=node-builder /app/dist/* /app/assets/

EXPOSE 8000

ENV PYTHONPATH=/app

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["api.main"]
