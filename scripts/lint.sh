#!/bin/bash

set -ex

poetry run mypy api
poetry run black --check --skip-string-normalization --diff api
poetry run isort --check-only --recursive api
