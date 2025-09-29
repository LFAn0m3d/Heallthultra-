#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

uvicorn app.main:app --host 0.0.0.0 --port 8000
