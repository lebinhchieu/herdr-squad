# Account 1 = ~/.claude (no CLAUDE_CONFIG_DIR, so it keeps ~/.claude.json),
# accounts 2 and 3 = ~/.claude-2 / ~/.claude-3 (own login + .claude.json; the rest symlinked to ~/.claude).
# Git Bash on Windows: the shared files are hardlinks and the shared folders junctions
# (symlinks need admin there); see relink.
ACCT_HOME="$HOME/.claude-accounts"; A_DIR="$HOME/.claude"
case "$(uname -s 2>/dev/null)" in MINGW*|MSYS*|CYGWIN*) CA_WIN=1 ;; *) CA_WIN=0 ;; esac
SHARED_FILES="CLAUDE.md settings.json settings.local.json .mcp.json statusline-command.sh"
SHARED_DIRS="skills plugins hooks themes projects agents commands output-styles"
SHARED="$SHARED_FILES $SHARED_DIRS"
WS_DIR="$ACCT_HOME/workspace-default"
ws_id_ok() { [[ "$1" =~ ^w[0-9A-Za-z]+$ ]]; } # the id becomes a file name: nothing else gets through
global_default() { local v; v=$(cat "$ACCT_HOME/default" 2>/dev/null); case "$v" in 1|2|3) echo "$v" ;; *) echo 1 ;; esac; }
# workspace default (herdr only) -> else the global one
default_account() {
  local v id="${HERDR_WORKSPACE_ID:-}"
  if [ "${HERDR_ENV:-}" = 1 ] && ws_id_ok "$id"; then
    v=$(cat "$WS_DIR/$id" 2>/dev/null)
    case "$v" in 1|2|3) echo "$v"; return ;; esac
  fi
  global_default
}
# $1 = workspace id, panel number or label -> prints the id. Tiers, first with a hit wins: id, panel number, label.
# More than one hit in the winning tier: candidates on stderr, rc 2. No hit: an id-shaped ref is taken as a raw id.
resolve_workspace() {
  local ref="$1" list hits n
  [[ "$ref" =~ [^[:space:]] ]] || { echo "no workspace matches $ref" >&2; return 2; }
  list=$(timeout 5 herdr workspace list 2>/dev/null) && jq -e '.result.workspaces' >/dev/null 2>&1 <<<"$list" || list=
  if [ -n "$list" ]; then
    hits=$(jq -r --arg r "$ref" '.result.workspaces as $w
      | ([$w[]|select(.workspace_id==$r)]) as $a
      | (if ($r|test("^[0-9]+$")) then [$w[]|select((.number|tostring)==$r)] else [] end) as $b
      | ([$w[]|select(.label==$r)]) as $c
      | (if ($a|length)>0 then $a elif ($b|length)>0 then $b else $c end)[]
      | "\(.workspace_id)\t\(.number)\t\(.label)"' <<<"$list" 2>/dev/null)
    n=$(grep -c . <<<"$hits")
    if [ "$n" -eq 1 ]; then local id; id=$(cut -f1 <<<"$hits"); ws_id_ok "$id" && { echo "$id"; return 0; }
    elif [ "$n" -gt 1 ]; then
      echo "ambiguous: $ref matches" >&2
      while IFS=$'\t' read -r id num lab; do echo "$id (panel $num) $lab" >&2; done <<<"$hits"
      return 2
    fi
  fi
  if ws_id_ok "$ref"; then echo "$ref"; return 0; fi
  echo "no workspace matches $ref" >&2; return 2
}
# Display-only account token for the herdr spaces panel; never changes the exit code, never prints. The epoch-ms seq makes herdr drop a late older report.
report_workspace_account() { # $1 = workspace id, $2 = 1|2|3
  timeout 3 herdr workspace report-metadata "$1" --source claude-accounts --token "account=c$2" --seq "$(date +%s%3N)" >/dev/null 2>&1 || true
}
# $1 = 1|2|3, $2 = workspace id (default $HERDR_WORKSPACE_ID, then only inside herdr).
# One file per workspace + atomic mv = parallel runs cannot lose each other's update.
set_workspace_default() {
  local acct="$1" id tmp ids f
  case "$acct" in 1|2|3) ;; *) return 2 ;; esac
  if [ -n "${2:-}" ]; then id="$2"
  else [ "${HERDR_ENV:-}" = 1 ] || return 0; id="${HERDR_WORKSPACE_ID:-}"; fi
  ws_id_ok "$id" || return 0
  mkdir -p "$WS_DIR" 2>/dev/null && tmp=$(mktemp "$WS_DIR/.tmp.XXXXXX" 2>/dev/null) || return 1
  if echo "$acct" > "$tmp" && mv -f "$tmp" "$WS_DIR/$id"; then :; else rm -f "$tmp"; return 1; fi
  report_workspace_account "$id" "$acct"
  # drop files of workspaces herdr no longer lists; do nothing if the list failed or is empty
  ids=$(timeout 5 herdr workspace list 2>/dev/null | jq -r '.result.workspaces[].workspace_id' 2>/dev/null) || return 0
  [ -n "$ids" ] || return 0
  for f in "$WS_DIR"/w*; do
    [ -f "$f" ] || continue
    f=${f##*/}
    ws_id_ok "$f" && [ "$f" != "$id" ] && ! grep -qxF "$f" <<<"$ids" && rm -f "$WS_DIR/$f"
  done
  return 0
}
acct_dir() { # $1 = 1|2|3 -> the account's config dir
  case "$1" in
    1) echo "$A_DIR" ;;
    2|3) echo "$HOME/.claude-$1" ;;
    *) return 2 ;;
  esac
}
win() { cygpath -w "$1"; }
# Windows: file symlinks need admin, so the shared files are hardlinks and the shared folders junctions. Claude may
# rewrite a file via rename, which silently splits a hardlink, so this re-joins it before every launch, keeping
# whichever copy is newer.
relink() { # $1 = the account dir (account 2 or 3) to join to account 1's shared files
  local d="$1" f a b
  for f in $SHARED_FILES; do
    a="$A_DIR/$f"; b="$d/$f"
    [ -e "$a" ] || [ -e "$b" ] || continue
    [ -e "$a" ] && [ -e "$b" ] && [ "$(ls -i "$a" | cut -d' ' -f1)" = "$(ls -i "$b" | cut -d' ' -f1)" ] && continue
    if [ -e "$b" ] && { [ ! -e "$a" ] || [ "$b" -nt "$a" ]; }; then cp -p "$b" "$a"; fi
    rm -f "$b"; ln "$a" "$b"
  done
  for f in $SHARED_DIRS; do
    mkdir -p "$A_DIR/$f"
    [ -e "$d/$f" ] || cmd //c mklink //J "$(win "$d/$f")" "$(win "$A_DIR/$f")" >/dev/null
  done
}
link_shared() { # $1 = 2|3
  local f d; d=$(acct_dir "$1") || return 2
  mkdir -p "$d"
  if [ "$CA_WIN" = 1 ]; then relink "$d"; return; fi
  for f in $SHARED; do
    [ -L "$d/$f" ] && continue
    [ -e "$A_DIR/$f" ] || continue
    rm -rf "$d/$f"; ln -s "$A_DIR/$f" "$d/$f"
  done
}
run_claude() { # $1 = 1|2|3, rest = claude args
  local acct="$1"; shift
  case "$acct" in
    1) env -u CLAUDE_CONFIG_DIR claude "$@" ;;
    2|3) link_shared "$acct"; CLAUDE_CONFIG_DIR=$(acct_dir "$acct") claude "$@" ;;
    *) echo "unknown account '$acct' (use 1, 2 or 3)" >&2; return 2 ;;
  esac
}
