#!/bin/bash

set -x

poetry run autoflake \
  --recursive \
  --remove-all-unused-imports \
  --remove-unused-variables \
  --in-place api \
  --exclude=__init__.py

poetry run black --skip-string-normalization api

poetry run isort \
  --recursive \
  --apply api
