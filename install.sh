#!/usr/bin/env bash
set -euxo pipefail

# Prerequisites: uv (https://docs.astral.sh/uv/).
# Installs project dependencies (incl. the dev group) and registers pre-commit hooks.

uv sync --dev
uv run pre-commit install

set +x
echo ""
echo "Setup complete."
echo "Run the kill test with:  uv run python -m killtest"
