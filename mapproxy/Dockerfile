FROM python:3.9-slim as base

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONFAULTHANDLER=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

ARG USER_ID=1000
ARG GROUP_ID=1000

RUN set -eux; \
    pip3 install mapproxy pyproj gunicorn; \
    groupadd -g ${GROUP_ID} mapproxy; \
    useradd -u ${USER_ID} -M -d /app -s /usr/sbin/nologin -g mapproxy mapproxy


COPY docker-entrypoint.sh /
COPY main.py mapproxy.yml /app/

EXPOSE 8000

USER mapproxy:mapproxy

WORKDIR /app

ENTRYPOINT ["/docker-entrypoint.sh"]

CMD [ \
  "--bind=0.0.0.0:8000", \
  "--workers=4", \
  "--threads=16", \
  "--access-logfile=-", \
  "--preload", \
  "--proxy-allow-from=*" \
]
