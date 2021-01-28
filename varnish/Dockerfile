FROM varnish:6.5.1-1

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.7.3/wait /wait
RUN set -eux; \
    chmod +x /wait; \
    sed -i 's!set --!/wait; set --!' /usr/local/bin/docker-varnish-entrypoint

ENV WAIT_HOSTS=mapproxy:8000,tileserver:8000

COPY varnish.vcl /etc/varnish/default.vcl
