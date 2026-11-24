# 02 Standing yes for routine gates

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md`
Duties: Design and technical AC: `$SCOPE_DIR/tasks/02-design-notes.md` (Tech Lead) with `$SCOPE_DIR/tasks/qaw-technical-ac.md` (QA whitebox, 02 and common lines). Write rule ITER-19 and edit every place the notes list; no version bump; lint exit 0; run the test files the notes list plus the SQ-10 trio; write `evidence.md`; HANDIN to both QAs.
Files: `$SCOPE_DIR/tasks/02-design-notes.md`, `templates/squad/process/iterations.md`, `templates/squad/process/closing.md`, `templates/squad/process/suites.md`, `templates/squad/process/goal.md`, `CLAUDE.md`, `tests/test_rules_wording.py`, `skills/squad-process-update/changelog.md`

## Problem

Many inbox items ask for a yes that Chieu always gives. On guardian `clarify` (22-23 Oct) the routine ones were:

| Item | Ask | Chieu's answer |
|---|---|---|
| E4, E5, E8, E9, E15, E23 | passed: confirm close | yes |
| E12 | plan14: start now? | yes |
| E2 | start sync14 and erd11? | yes |

So 8 of 24 items were routine.

## Change

There is a new rule in `iterations.md`: a gate on the **routine list** goes ahead without asking. The Manager sends one `read` item (an `[info]` notice), not an `answer` item. Chieu can still say "undo" in chat.

```diagram Before and after, for a passed scope
BEFORE: passed -> answer item -> wait
        -> Chieu: "close" -> close
▼
AFTER:  passed -> close -> read item
        "[info] erd13 closed; say undo"
```

**Gate list (Chieu, 2026-11-24):**

| Gate | Kind | What happens |
|---|---|---|
| Close a passed scope, 0 open findings | [ok] routine | goes ahead, `[info]` notice |
| Start the next scope already in the agreed plan | [ok] routine | goes ahead, `[info]` notice |
| Full `--tz` suite on the final sha | [warn] ask, non-blocking | asked, work goes on |
| Merge, push, deploy | [fail] always asks | ADR 0027 |
| Team, plan or scope change | [fail] always asks | Chieu's call |

**Non-blocking ask (full suite):** the Manager sends an `answer` item with no `--blocks`. Nothing waits on it: tasks keep moving, and the scope may pass and close. The answer is needed only before a **merge**. When Chieu says yes, the suite owner runs it at once. When the merge comes and there is still no answer, the merge item says so in its verdict line.

```diagram Full-suite ask, non-blocking
final sha ready -> ask "full suite?"
▼
team goes on: close, next scope
▼
Chieu: yes -> suite owner runs --tz
▼
merge item shows the suite result
```

## AC

- AC1: the rule names exactly the gates in the table above, and `squad-process lint` exits 0.
- AC1b: the full-suite ask has no `--blocks`; the rule says the team never waits on it and the merge item names a missing answer. The "Running tests" lines in the repo `CLAUDE.md` and the suite rule (`--tz` asks Chieu) say the same.
- AC2: a scope with `away` set behaves as before (ITER-17 is unchanged).
- AC3: the routine notice is a `read` item with an `[info]` verdict line and the word "undo".
- AC4: changelog entry and plugin version bump.

## Comments
