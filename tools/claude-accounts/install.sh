#!/usr/bin/env bash
# Links ~/.claude-accounts and ~/.claude/skills/claude-accounts to this checkout, per file.
# ~/.claude-accounts stays a real directory so its state files (default, workspace-default/, usage-*, cswitch.log) stay put.
# Usage: install.sh [--dry-run] [--force] [--allow-worktree]
#   --force           replace a live file whose content differs from the repo's (default: stop, change nothing)
#   --allow-worktree  run from a git worktree anyway (tests only: a worktree is deleted when its squad closes)
set -u
DRY=0 FORCE=0 WT=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;; --force) FORCE=1 ;; --allow-worktree) WT=1 ;;
    *) echo "usage: install.sh [--dry-run] [--force] [--allow-worktree]" >&2; exit 2 ;;
  esac
done
SRC=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
ACCT="$HOME/.claude-accounts"
SKILL_LINK="$HOME/.claude/skills/claude-accounts"
rc=0
W=; [ "$DRY" = 1 ] && W="would "

gd=$(git -C "$SRC" rev-parse --absolute-git-dir 2>/dev/null)
gc=$(git -C "$SRC" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
if [ -n "$gd" ] && [ "$gd" != "$gc" ]; then
  if [ "$WT" = 1 ]; then echo "warning: running from a git worktree ($SRC); links break when it is removed"
  else echo "error: $SRC is a git worktree and will be deleted; run install.sh from the main checkout" >&2; exit 1; fi
fi

TOOL=(lib.sh usage-popup.sh record-usage.sh HANDOFF.md); for f in "$SRC"/bin/*; do TOOL+=("bin/${f##*/}"); done
is_leftover() { case "${1##*/}" in *.bak|*.bak-*|*.new|*.orig|__pycache__) return 0 ;; esac; return 1; }
is_state() { case "$1" in default|usage-[0-9]*|cswitch.log|workspace-default|.git) return 0 ;; esac; return 1; }
is_tool() { local t; for t in "${TOOL[@]}"; do [ "$t" = "$1" ] && return 0; done; return 1; }
real_file() { [ -f "$1" ] && [ ! -L "$1" ]; }
real_dir() { [ -d "$1" ] && [ ! -L "$1" ]; }

echo "installing from: $SRC"
# Checks first: nothing changes unless every file passes.
refuse=()
blocked=" "
check_file() { # $1 = repo file, $2 = live path
  if real_dir "$2"; then refuse+=("$2 is a directory"); blocked+="$2 "
  elif real_file "$2" && ! cmp -s "$1" "$2" && [ "$FORCE" = 0 ]; then
    refuse+=("$2 differs from the repo's file; see: diff '$2' '$1'  (--force replaces it)"); blocked+="$2 "
  fi
}
for t in "${TOOL[@]}"; do check_file "$SRC/$t" "$ACCT/$t"; done
if real_dir "$SKILL_LINK"; then
  check_file "$SRC/skill/SKILL.md" "$SKILL_LINK/SKILL.md"
  for f in "$SKILL_LINK"/* "$SKILL_LINK"/.[!.]*; do
    [ -e "$f" ] || [ -L "$f" ] || continue
    [ "${f##*/}" = SKILL.md ] || is_leftover "$f" || { refuse+=("$f is not part of the skill; move it away, the folder becomes a link"); blocked+="$SKILL_LINK "; }
  done
elif [ -e "$SKILL_LINK" ] && [ ! -L "$SKILL_LINK" ]; then refuse+=("$SKILL_LINK is not a directory or link"); blocked+="$SKILL_LINK "; fi
if [ "${#refuse[@]}" -gt 0 ]; then
  for m in "${refuse[@]}"; do echo "refused: $m" >&2; done
  [ "$DRY" = 1 ] || { echo "nothing changed" >&2; exit 1; }
  rc=1
fi

do_() { [ "$DRY" = 1 ] || "$@" || rc=1; }
link() { # $1 = repo file or dir, $2 = link path
  case "$blocked" in *" $2 "*) echo "would refuse: $2"; return ;; esac
  if [ -L "$2" ] && [ "$(readlink "$2")" = "$1" ]; then echo "ok: $2"; return; fi
  echo "${W}link: $2 -> $1"; do_ ln -sfn "$1" "$2"
}
clean() { # delete leftovers directly inside real directory $1
  real_dir "$1" || return 0
  local f
  for f in "$1"/* "$1"/.[!.]*; do
    [ -e "$f" ] || [ -L "$f" ] || continue
    [ "$f" = "$1/.git" ] && continue
    is_leftover "$f" && { echo "${W}delete: $f"; do_ rm -rf "$f"; }
  done
}

[ "$DRY" = 1 ] || mkdir -p "$ACCT/bin" "$HOME/.claude/skills"
for t in "${TOOL[@]}"; do link "$SRC/$t" "$ACCT/$t"; done

if real_dir "$SKILL_LINK" && [[ "$blocked" != *" $SKILL_LINK "* ]]; then
  clean "$SKILL_LINK"
  echo "${W}replace directory with a link: $SKILL_LINK"
  do_ rm -f "$SKILL_LINK/SKILL.md"; do_ rmdir "$SKILL_LINK"
fi
real_dir "$SKILL_LINK" && [ "$DRY" = 0 ] || link "$SRC/skill" "$SKILL_LINK"

clean "$ACCT"; clean "$ACCT/bin"
for d in "$ACCT" "$ACCT/bin"; do
  real_dir "$d" || continue
  for f in "$d"/* "$d"/.[!.]*; do
    [ -e "$f" ] || [ -L "$f" ] || continue
    rel=${f#"$ACCT"/}
    is_tool "$rel" || is_state "$rel" || is_leftover "$f" || [ "$rel" = bin ] || echo "kept: $f (not part of the tool)"
  done
done
[ -e "$ACCT/.git" ] && echo ".git in $ACCT was left alone; retire it by hand when satisfied."
exit $rc
