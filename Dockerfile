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
FROM debian:bullseye-slim as base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1

RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get -y --no-install-recommends install \
        python3; \
    apt-get -y --purge autoremove; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

#
# API builder
#
FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

#RUN apk add --no-cache build-base libressl-dev libffi-dev gcc musl-dev gdal-dev \
#    python3-dev libxml2-dev libxslt-dev postgresql-dev geos-dev proj-dev proj-util


RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get -y --no-install-recommends install \
        python3-dev \
        python3-pip \
        python3-venv \
        build-essential \
        libpq-dev \
        libproj-dev \
        proj-bin \
        libgdal-dev; \
    apt-get -y --purge autoremove; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    pip3 install -U poetry


COPY pyproject.toml poetry.lock ./

ARG BUILD_ENV=dev

RUN set -eux; \
    python3 -m venv /venv; \
    POETRY_ARGS=""; \
    [ "${BUILD_ENV}" = "dev" ] && POETRY_ARGS="--dev"; \
    poetry export $POETRY_ARGS -f requirements.txt \
        | /venv/bin/pip install -r /dev/stdin


#
# Final
#
FROM base as final

#RUN apk add --no-cache libffi libpq geos proj-util gdal

RUN set -eux; \
    export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get -y --no-install-recommends install \
        python3-distutils \
        proj-bin \
        libgdal28; \
    apt-get -y --purge autoremove; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /venv /venv
COPY . ./
COPY --from=node-builder /app/dist/* /app/assets/

EXPOSE 8000

ENV PYTHONPATH=/app \
    BIND_HOST=0.0.0.0 \
    BIND_PORT=8000

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["api.main"]
