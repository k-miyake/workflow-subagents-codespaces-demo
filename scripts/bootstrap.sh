#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3, 13), "Python 3.13+ is required"'
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/settings.py init
mkdir -p .demo/reports
bash scripts/welcome.sh
