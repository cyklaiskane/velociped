#!/bin/bash

set -eo pipefail

context=${DOCKER_CONTEXT:-docker3}

docker --context ${context} stack deploy --prune -c <(docker-compose -f docker-compose.yml -f docker-compose-prod.yml config) cyklaiskane
