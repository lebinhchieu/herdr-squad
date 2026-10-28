# Delivery probe (additionalContext reaches the model)

Command (from a dir with `hook.sh` and `settings.json` in this folder; path in settings adjusted to `/tmp/probe12/`):

    claude -p "Run the bash command 'echo hi'. Then quote verbatim any hook additional context you saw after it." \
      --settings /tmp/probe12/settings.json --allowedTools Bash < /dev/null

Output (model reply, 2026-10-22):

    Output: `hi`
    Hook additional context, verbatim:
    > PostToolUse:Bash hook additional context: CANARY-9902 notice from hook
