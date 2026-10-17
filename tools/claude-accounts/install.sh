#!/usr/bin/env bash
# Links ~/.claude-accounts and ~/.claude/skills/claude-accounts to this checkout, per file.
# ~/.claude-accounts stays a real directory so its state files (default, workspace-default/, usage-*, cswitch.log) stay put.
# Usage: install.sh [--dry-run]
set -u
DRY=0
case "${1:-}" in
  "") ;;
  --dry-run) DRY=1 ;;
  *) echo "usage: install.sh [--dry-run]" >&2; exit 2 ;;
esac
SRC=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
ACCT="$HOME/.claude-accounts"
SKILL_LINK="$HOME/.claude/skills/claude-accounts"
rc=0

do_() { if [ "$DRY" = 1 ]; then echo "would: $*"; else echo "$*"; "$@" || rc=1; fi; }

link() { # $1 = repo file or dir, $2 = link path
  if [ -L "$2" ] && [ "$(readlink "$2")" = "$1" ]; then echo "ok: $2"; return; fi
  if [ -d "$2" ] && [ ! -L "$2" ]; then echo "error: $2 is a real directory; not replacing it" >&2; rc=1; return; fi
  do_ ln -sfn "$1" "$2"
}

clean() { # delete leftovers directly inside real directory $1
  [ -d "$1" ] && [ ! -L "$1" ] || return 0
  find "$1" -maxdepth 1 \( -name '*.bak' -o -name '*.bak-*' -o -name '*.new' -o -name '*.orig' \) -type f -print0 |
    while IFS= read -r -d '' f; do do_ rm -f "$f"; done
  find "$1" -maxdepth 1 -name __pycache__ -type d -print0 |
    while IFS= read -r -d '' f; do do_ rm -rf "$f"; done
}

do_ mkdir -p "$ACCT/bin" "$HOME/.claude/skills"
for f in "$SRC"/bin/* "$SRC"/lib.sh "$SRC"/usage-popup.sh "$SRC"/record-usage.sh "$SRC"/HANDOFF.md; do
  rel=${f#"$SRC"/}
  link "$f" "$ACCT/$rel"
done

# A skill directory left by an older install holds only the skill and leftovers; replace it with the link.
if [ -d "$SKILL_LINK" ] && [ ! -L "$SKILL_LINK" ]; then
  clean "$SKILL_LINK"
  if [ "$DRY" = 1 ]; then echo "would: replace directory $SKILL_LINK with a link"
  else
    rm -f "$SKILL_LINK/SKILL.md"
    rmdir "$SKILL_LINK" 2>/dev/null || { echo "error: $SKILL_LINK has other files; not replacing it" >&2; rc=1; }
  fi
fi
[ -d "$SKILL_LINK" ] && [ ! -L "$SKILL_LINK" ] || link "$SRC/skill" "$SKILL_LINK"

clean "$ACCT"; clean "$ACCT/bin"
exit $rc
