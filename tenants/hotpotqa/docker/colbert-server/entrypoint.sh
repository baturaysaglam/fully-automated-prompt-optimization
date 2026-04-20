#!/usr/bin/env bash
set -euo pipefail

DATA_DIR="${DATA_DIR:-/app/data}"
PORT="${PORT:-8893}"

exec python start_colbert_server.py --data-dir "$DATA_DIR" --port "$PORT"
