#!/bin/sh

set -e

. /venv/bin/activate

# first arg is not an executable
if ! which -- "${1}"; then
  set -- python -m "$@"
fi

exec "$@"
