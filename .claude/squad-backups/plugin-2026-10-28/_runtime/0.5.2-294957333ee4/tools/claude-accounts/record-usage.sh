#!/usr/bin/env bash
# Called from the Claude status line:
#   record-usage.sh SESSION_ID FIVE_PCT FIVE_RESETS WEEK_PCT WEEK_RESETS
# Caches this account's usage for usage-popup.sh.
H="$HOME/.claude-accounts"
acct=1; [ -n "${CLAUDE_CONFIG_DIR:-}" ] && acct="${CLAUDE_CONFIG_DIR##*-}"
[ -n "$2" ] && echo "$2 $3 $4 $5 $(date +%s)" > "$H/usage-$acct"
