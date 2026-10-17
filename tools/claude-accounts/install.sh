#!/usr/bin/env bash
# Links ~/.claude-accounts and ~/.claude/skills/claude-accounts to this checkout, per file.
# ~/.claude-accounts stays a real directory so its state files (default, workspace-default/, usage-*, cswitch.log) stay put.
# Usage: install.sh [--dry-run] [--force] [--allow-worktree] [--unlink]
#   --dry-run         print the whole plan, change nothing (exit 1 when a real run would refuse)
#   --force           replace a live file or skill folder whose content differs, after moving it to ~/.claude-accounts/.install-backup/
#   --allow-worktree  run from a linked git worktree anyway (tests only: a worktree is deleted when its squad closes)
#   --unlink          rollback: turn every link made here back into a regular copy of its target
set -u
DRY=0 FORCE=0 WT=0 UNLINK=0
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;; --force) FORCE=1 ;; --allow-worktree) WT=1 ;; --unlink) UNLINK=1 ;;
    *) echo "usage: install.sh [--dry-run] [--force] [--allow-worktree] [--unlink]" >&2; exit 2 ;;
  esac
done
if [ -z "${HOME:-}" ] || [ ! -d "$HOME" ]; then echo "error: HOME is empty or not a directory" >&2; exit 2; fi
SRC=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
ACCT="$HOME/.claude-accounts"
SKILL_LINK="$HOME/.claude/skills/claude-accounts"
BACKUP="$ACCT/.install-backup"
rc=0
W=; [ "$DRY" = 1 ] && W="would "
echo "installing from: $SRC"

gd=$(git -C "$SRC" rev-parse --absolute-git-dir 2>/dev/null)
gc=$(git -C "$SRC" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
if [ -n "$gd" ] && [ "$gd" != "$gc" ]; then
  if [ "$WT" = 1 ]; then echo "warning: running from a git worktree; links break when it is removed"
  else echo "error: $SRC is in a git worktree that is deleted when its squad closes; run install.sh from the main checkout" >&2; exit 1; fi
fi

BINS=(); for f in "$SRC"/bin/*; do BINS+=("${f##*/}"); done
TOP=(lib.sh usage-popup.sh record-usage.sh HANDOFF.md)
TOOL=("${TOP[@]}"); for b in "${BINS[@]}"; do TOOL+=("bin/$b"); done

real_file() { [ -f "$1" ] && [ ! -L "$1" ]; }
real_dir() { [ -d "$1" ] && [ ! -L "$1" ]; }
in_list() { local x="$1"; shift; local y; for y in "$@"; do [ "$x" = "$y" ] && return 0; done; return 1; }
# Every rm / mv path must sit under the live home or the skill link.
under() { case "$1" in "$ACCT"/*|"$SKILL_LINK"|"$SKILL_LINK"/*) return 0 ;; esac; echo "error: refusing to touch $1" >&2; rc=1; return 1; }
do_rm() { under "$1" || return; [ "$DRY" = 1 ] || rm -f "$1" || rc=1; }
do_rmdir() { under "$1" || return; [ "$DRY" = 1 ] || rmdir "$1" || rc=1; }
do_mv() { under "$1" && under "$2" || return; [ "$DRY" = 1 ] || mv -T "$1" "$2" || rc=1; }
swap() { # atomic: temp link in the same directory, then rename over the target
  local tmp="$2.install-tmp"
  under "$2" || return
  [ "$DRY" = 1 ] && return
  rm -f "$tmp"
  if ln -s "$1" "$tmp" && mv -T "$tmp" "$2"; then :; else rm -f "$tmp"; rc=1; fi
}
backup() { # move $1 (path under the live home / skill link) into .install-backup/
  local dest="$BACKUP/${2}"
  [ -e "$dest" ] || [ -L "$dest" ] && dest="$dest.$(date +%s)"
  echo "${W}backup: $1 -> $dest"
  under "$1" || return
  [ "$DRY" = 1 ] || { mkdir -p "$(dirname "$dest")" && mv -T "$1" "$dest"; } || rc=1
}

classify_file() { # $1 = live path, $2 = repo file -> ok | link | repoint | identical | differs | dir | other
  if [ -L "$1" ]; then [ "$(readlink "$1")" = "$2" ] && echo ok || echo repoint
  elif [ ! -e "$1" ]; then echo link
  elif [ -d "$1" ]; then echo dir
  elif [ -f "$1" ]; then cmp -s "$2" "$1" && echo identical || echo differs
  else echo other; fi
}

# A leftover is a regular file or link "<managed name>.bak-*|.new|.orig", or a __pycache__ holding only *.pyc.
is_leftover() { # $1 = path, rest = managed names
  local p="$1" n; shift
  local b=${p##*/}
  if [ "$b" = __pycache__ ] && real_dir "$p"; then
    local f; for f in "$p"/* "$p"/.[!.]*; do [ -e "$f" ] || [ -L "$f" ] || continue; case "$f" in *.pyc) real_file "$f" || return 1 ;; *) return 1 ;; esac; done
    return 0
  fi
  [ -d "$p" ] && [ ! -L "$p" ] && return 1
  for n in "$@"; do case "$b" in "$n".bak-*|"$n".new|"$n".orig) return 0 ;; esac; done
  return 1
}
leftovers() { # $1 = directory, rest = managed names; prints each leftover path
  local d="$1"; shift
  real_dir "$d" || return 0
  local f; for f in "$d"/* "$d"/.[!.]*; do { [ -e "$f" ] || [ -L "$f" ]; } && is_leftover "$f" "$@" && echo "$f"; done
}
delete_leftover() {
  local f="$1"
  if [ -d "$f" ] && [ ! -L "$f" ]; then
    local g; for g in "$f"/*; do [ -e "$g" ] || continue; echo "${W}delete: $g"; do_rm "$g"; done
    echo "${W}delete: $f"; do_rmdir "$f"
  else echo "${W}delete: $f"; do_rm "$f"; fi
}

# ---- --unlink: rollback ----
if [ "$UNLINK" = 1 ]; then
  for t in "${TOOL[@]}"; do
    d="$ACCT/$t"
    [ -L "$d" ] && [ "$(readlink "$d")" = "$SRC/$t" ] || continue
    echo "${W}unlink: $d (regular copy)"
    if [ "$DRY" = 0 ]; then under "$d" && cp -p "$SRC/$t" "$d.install-tmp" && mv -T "$d.install-tmp" "$d" || { rm -f "$d.install-tmp"; rc=1; }; fi
  done
  if [ -L "$SKILL_LINK" ] && [ "$(readlink "$SKILL_LINK")" = "$SRC/skill" ]; then
    echo "${W}unlink: $SKILL_LINK (real directory copy)"
    if [ "$DRY" = 0 ]; then
      under "$SKILL_LINK" && rm -rf "$SKILL_LINK.install-tmp" && mkdir "$SKILL_LINK.install-tmp" && cp -rp "$SRC/skill/." "$SKILL_LINK.install-tmp" \
        && rm -f "$SKILL_LINK" && mv -T "$SKILL_LINK.install-tmp" "$SKILL_LINK" || rc=1
    fi
  fi
  exit $rc
fi

# ---- preflight: decide everything first; one refusal changes nothing ----
declare -A blocked
refuse() { echo "refused: $1" >&2; blocked["$2"]=1; REFUSED=1; }
REFUSED=0
for d in "$ACCT" "$ACCT/bin"; do
  if [ -e "$d" ] || [ -L "$d" ]; then real_dir "$d" || refuse "$d is not a real directory" "$d"; fi
done
for t in "${TOOL[@]}"; do
  d="$ACCT/$t"; [ -n "${blocked[$ACCT]+x}" ] && break
  case $(classify_file "$d" "$SRC/$t") in
    dir) refuse "$d is a directory" "$d" ;;
    other) refuse "$d is not a regular file or link" "$d" ;;
    differs) [ "$FORCE" = 1 ] || refuse "$d differs from the repo's file; see: diff '$d' '$SRC/$t'  (--force moves it to $BACKUP first)" "$d" ;;
  esac
done
SKILL_STATE=link
if [ -L "$SKILL_LINK" ]; then [ "$(readlink "$SKILL_LINK")" = "$SRC/skill" ] && SKILL_STATE=ok || SKILL_STATE=repoint
elif real_dir "$SKILL_LINK"; then
  SKILL_STATE=replace
  for f in "$SKILL_LINK"/* "$SKILL_LINK"/.[!.]*; do
    { [ -e "$f" ] || [ -L "$f" ]; } || continue
    if [ "${f##*/}" = SKILL.md ]; then
      real_file "$f" && cmp -s "$SRC/skill/SKILL.md" "$f" || { SKILL_STATE=differs; SKILL_WHY="$f differs from the repo's file; see: diff '$f' '$SRC/skill/SKILL.md'"; }
    elif ! is_leftover "$f" SKILL.md; then SKILL_STATE=differs; SKILL_WHY="$f is not part of the skill"; fi
  done
  if [ "$SKILL_STATE" = differs ] && [ "$FORCE" = 0 ]; then refuse "$SKILL_WHY  (--force moves the folder to $BACKUP first)" "$SKILL_LINK"; fi
elif [ -e "$SKILL_LINK" ]; then refuse "$SKILL_LINK is not a directory or link" "$SKILL_LINK"; fi
if [ "$REFUSED" = 1 ]; then
  [ "$DRY" = 1 ] || { echo "nothing changed" >&2; exit 1; }
  rc=1
fi

# ---- apply ----
[ "$DRY" = 1 ] || mkdir -p "$ACCT/bin" "$HOME/.claude/skills" || exit 1
for t in "${TOOL[@]}"; do
  d="$ACCT/$t"
  [ -n "${blocked[$d]+x}" ] && { echo "would refuse: $d"; continue; }
  [ -n "${blocked[$ACCT]+x}" ] && continue
  case $(classify_file "$d" "$SRC/$t") in
    ok) echo "ok: $d" ;;
    link) echo "${W}link: $d -> $SRC/$t"; swap "$SRC/$t" "$d" ;;
    repoint) echo "${W}repoint: $d -> $SRC/$t"; swap "$SRC/$t" "$d" ;;
    identical) echo "${W}link: $d (identical copy replaced) -> $SRC/$t"; swap "$SRC/$t" "$d" ;;
    differs) backup "$d" "$t"; echo "${W}link: $d -> $SRC/$t"; swap "$SRC/$t" "$d" ;;
  esac
done

if [ -n "${blocked[$SKILL_LINK]+x}" ]; then echo "would refuse: $SKILL_LINK"
else
  case $SKILL_STATE in
    ok) echo "ok: $SKILL_LINK" ;;
    link|repoint) echo "${W}$SKILL_STATE: $SKILL_LINK -> $SRC/skill"; swap "$SRC/skill" "$SKILL_LINK" ;;
    replace)
      echo "${W}replace directory: $SKILL_LINK -> $SRC/skill"
      for f in "$SKILL_LINK"/* "$SKILL_LINK"/.[!.]*; do
        { [ -e "$f" ] || [ -L "$f" ]; } || continue
        if [ -d "$f" ] && [ ! -L "$f" ]; then delete_leftover "$f"; else do_rm "$f"; fi
      done
      do_rmdir "$SKILL_LINK"; [ "$rc" = 0 ] && swap "$SRC/skill" "$SKILL_LINK" ;;
    differs) backup "$SKILL_LINK" skill; swap "$SRC/skill" "$SKILL_LINK" ;;
  esac
fi

# Leftovers go only when every link above worked.
if [ "$rc" = 0 ]; then
  while IFS= read -r f; do [ -n "$f" ] && delete_leftover "$f"; done < <(leftovers "$ACCT" "${TOP[@]}"; leftovers "$ACCT/bin" "${BINS[@]}")
fi

for d in "$ACCT" "$ACCT/bin" "$ACCT/workspace-default"; do
  real_dir "$d" || continue
  for f in "$d"/* "$d"/.[!.]*; do
    { [ -e "$f" ] || [ -L "$f" ]; } || continue
    rel=${f#"$ACCT"/}
    case "$d" in
      "$ACCT") in_list "$rel" "${TOP[@]}" bin workspace-default default cswitch.log .git .install-backup && continue
               case "$rel" in usage-[0-9]) continue ;; esac
               is_leftover "$f" "${TOP[@]}" && [ "$rc" = 0 ] && continue ;;
      "$ACCT/bin") in_list "$rel" "${TOOL[@]}" && continue; is_leftover "$f" "${BINS[@]}" && [ "$rc" = 0 ] && continue ;;
      *) [[ "${f##*/}" =~ ^w[0-9A-Za-z]+$ ]] && continue ;;
    esac
    echo "unexpected: $f (kept)"
  done
done
[ -e "$ACCT/.git" ] && echo "$ACCT/.git was left alone; retire it by hand when satisfied."
exit $rc
