#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo "Bootstrap complete."
echo "Next:"
echo "  1. source .venv/bin/activate"
echo "  2. python scripts/create_api_key.py --owner local-dev"
echo "  3. make run"
