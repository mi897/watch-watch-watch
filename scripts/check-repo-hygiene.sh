#!/usr/bin/env bash
# Fails if a real config/secret is tracked, or a compose file uses :latest.
set -euo pipefail
cd "$(dirname "$0")/.."
bad=$(git ls-files | grep -E '(^|/)(\.env|config\.ya?ml|.*\.(db|sqlite3?|key|pem))$' || true)
if [ -n "$bad" ]; then echo "Tracked secret/config files:"; echo "$bad"; exit 1; fi
unpinned=$(git ls-files 'compose*.y*ml' | xargs -r grep -hE '^\s*image:' | grep -vE 'image:\s*\S+:[^ :@]+(@sha256:\S+)?\s*$' || true)
unpinned="$unpinned$(git ls-files 'compose*.y*ml' | xargs -r grep -hE 'image:.*:latest' || true)"
if [ -n "$unpinned" ]; then echo "Unpinned image(s):"; echo "$unpinned"; exit 1; fi
echo "hygiene ok"
