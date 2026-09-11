#!/usr/bin/env bash
set -euo pipefail
cat <<'TEXT'

Dynamic Workflows demo (Preview)
  1. ./demo configure       Set your existing Foundry project and model deployment
  2. az login --use-device-code
  3. ./demo doctor
  4. ./demo start           Keep this terminal running
  5. ./demo submit --wait   Run in a second terminal

Ports: 8082 = DTS dashboard / 8000 = generated report
PR data is synthetic. Model inference is live and billable.
See README.md for the Japanese walkthrough.
TEXT
