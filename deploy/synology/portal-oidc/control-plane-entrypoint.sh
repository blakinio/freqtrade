#!/bin/sh
set -eu

python -m ai_platform.portal.database.cli check
exec "$@"
