FROM maptiler/tileserver-gl:v3.1.1


# Hack! Tileserver does not retry if it can't connect to a layer source. Wait for API
# to become available by monkeypatching the entrypoint script.
USER root
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN set -eux; \
    chmod +x /wait; \
    sed -i 's!xvfb-run!/wait; xvfb-run!' /app/docker-entrypoint.sh

ENV WAIT_HOSTS=api:8000

USER node

COPY * /data/
