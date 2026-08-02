#!/usr/bin/env bash
# Deprecated entrypoint kept only for old bookmarked raw.githubusercontent.com links
# against the public rhwallet-rhagent mirror. Always use the canonical URL directly —
# it is hosted on rhagent.bot and lives in the public Rhagent repo (skill/connect/bin/cli.js).
# Usage: curl -fsSL https://rhagent.bot/scripts/rh-connect.sh | bash

set -euo pipefail

CANONICAL="${RH_CONNECT_URL:-https://rhagent.bot/scripts/rh-connect.sh}"

echo "→ rh-connect.sh moved to the public Rhagent repo."
echo "→ Fetching: $CANONICAL"
exec bash -c "$(curl -fsSL "$CANONICAL")" -- "$@"
