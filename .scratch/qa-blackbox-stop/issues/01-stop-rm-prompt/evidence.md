# 01 evidence

## Behaviour
- AC1 cause: in this session the shell cwd was set to a `mktemp -d` dir, then `rm -rf "/tmp/tmp.XXXX"` (literal path) ran; the shell then reported `getcwd: cannot access parent directories`, so the removed dir was the cwd. This session's permission mode did not show the prompt, so the prompt itself was not reproduced here. The PO's message ("working directory or its ancestor") plus the literal path (SAFE-11 already followed) leave cwd-inside-the-dir as the only cause. Seen: cwd==removed dir; not seen: the prompt.
- AC2: SAFE-11 now reads: "Make scratch dirs with `mktemp -d`; `cd` out before `rm` (Claude blocks the cwd or a parent). No bare `rm -rf $VAR`: use `"${VAR:?}"` or a literal." Roles unchanged (dev, qa-whitebox, qa-blackbox).
- AC3: `squad-process lint` clean before and after (no output). `python3 -B tests/test_dev_rules_size.py`: OK; new assert pins the `cd` clause for all three roles. First try was 5128 B vs 5120 pin, so the wording was trimmed to fit.
- AC4: suite receipt in `$SCOPE_DIR/evidence/suite-default.txt`.
- AC5: `promote.md` here.

## Review
(filled after review)
