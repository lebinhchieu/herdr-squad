#!/usr/bin/env bash
# Called from the Claude status line:
#   record-usage.sh SESSION_ID FIVE_PCT FIVE_RESETS WEEK_PCT WEEK_RESETS
# Caches this account's usage for usage-popup.sh.
H="$HOME/.claude-accounts"
# The folder name decides the account: .claude-2 = 2, .claude-3 = 3, else 1. Either slash style.
acct=1; d=${CLAUDE_CONFIG_DIR:-}; d=${d//\\//}
case "${d##*/}" in .claude-2) acct=2 ;; .claude-3) acct=3 ;; esac
[ -n "$2" ] && echo "$2 $3 $4 $5 $(date +%s)" > "$H/usage-$acct"
