FROM node:lts-alpine as node-builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . ./

ENV NODE_ENV=production \
    APP_API_URI=''

RUN npm run build


FROM python:3.7-alpine as base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1

WORKDIR /app

FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apk add --no-cache build-base libressl-dev libffi-dev gcc musl-dev \
      python3-dev libxml2-dev libxslt-dev postgresql-dev geos-dev

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

ARG BUILD_ENV=dev

RUN set -euxo pipefail; \
    python -m venv /venv; \
    POETRY_ARGS=""; \
    [ "${BUILD_ENV}" = "dev" ] && POETRY_ARGS="--dev"; \
    poetry export $POETRY_ARGS -f requirements.txt \
      | /venv/bin/pip install -r /dev/stdin


# Final
FROM base as final

RUN apk add --no-cache libffi libpq geos

COPY --from=builder /venv /venv
COPY . ./
COPY --from=node-builder /app/dist/* /app/static/

EXPOSE 8080

ENV PYTHONPATH=/app

ENTRYPOINT ["./docker-entrypoint.sh"]

CMD ["api.main"]
