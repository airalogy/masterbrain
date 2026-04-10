#!/usr/bin/env bash

set -euo pipefail

API_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$API_DIR"
uv run masterbrain-build-desktop "$@"
