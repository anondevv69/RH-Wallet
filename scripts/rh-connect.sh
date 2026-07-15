#!/usr/bin/env bash
# Deprecated entrypoint — rhwallet-rhagent is private, so raw.githubusercontent.com 404s.
# Canonical script lives in the public Rhagent repo / on rhagent.bot.
# Usage: curl -fsSL https://rhagent.bot/scripts/rh-connect.sh | bash

set -euo pipefail

CANONICAL="${RH_CONNECT_URL:-https://rhagent.bot/scripts/rh-connect.sh}"

echo "→ rh-connect.sh moved to the public Rhagent repo."
echo "→ Fetching: $CANONICAL"
exec bash -c "$(curl -fsSL "$CANONICAL")" -- "$@"
