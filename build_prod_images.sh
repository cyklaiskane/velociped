#!/bin/bash

DOCKER_BUILDKIT=1 docker build -t trivectortraffic/cyklaiskane-tileserver -f Dockerfile.tileserver .
DOCKER_BUILDKIT=1 docker build -t trivectortraffic/cyklaiskane-varnish -f Dockerfile.varnish .
