#!/bin/sh

set -e

if ! which -- "${1}"; then
  # first arg is not an executable
  set -- gunicorn "$@" main:app
fi

exec "$@"
