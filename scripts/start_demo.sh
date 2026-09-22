#!/bin/bash
# Local rehearsal: preserve completed records and the shared model admission guard.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ] || [ ! -f data/durable.db ]; then
  echo 'This demo needs the existing Python environment and saved data/durable.db.'
  exit 1
fi
if /usr/sbin/lsof -nP -iTCP:8810 -sTCP:LISTEN >/dev/null 2>&1; then
  .venv/bin/python scripts/demo_preflight.py
  echo 'Existing demo server verified. Open http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7'
  exit 0
fi
set -a
source .env.example
set +a
export LASTBUY_AUTH_MODE=local-demo
export LASTBUY_DATABASE_URL=sqlite:///data/durable.db
# This launcher uses the local review server, without a second Durable dispatcher.
unset LASTBUY_DURABLE_URL LASTBUY_DURABLE_IN_PROCESS
echo 'Keep this terminal open. Demo: http://127.0.0.1:8810/?case=LTB-CLOUD-RELEASE-7'
exec .venv/bin/uvicorn lastbuy.api:create_app --factory --host 127.0.0.1 --port 8810
