#!/bin/bash

set -ex

poetry run mypy api
poetry run black --check api
poetry run isort --check-only --recursive api
