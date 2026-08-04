#!/bin/sh
set -eu

if [ "${1:-}" = "uvicorn" ]; then
    python -m ai_platform.portal.database.cli check
fi
exec "$@"
