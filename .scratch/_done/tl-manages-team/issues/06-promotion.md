# T6 · promotion: ADR 0010 and CONTEXT.md
Status: ready-for-agent
Type: task
Blocked by: none
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches (and no others)
`docs/adr/0010-team-lead-runs-the-pod.md` (new), `docs/adr/0006-process-writing-rule.md` (one added line under Status), `docs/adr/0008-spawn-overrides-survive-respawn.md` (one added line under Status, wording in `promote.md`), `CONTEXT.md`.

## Do
Write what `$SCOPE_DIR/promote.md` lists, by the project's rule (`/domain-modeling`: glossary terms in `CONTEXT.md`, decisions in `docs/adr/NNNN-<slug>.md`). Follow the form of ADR 0005 to 0009 (Status, Decision, Why, Consequences, Alternative rejected). Cite ADR 0005 (version bump). ADR 0006: add under its Status line `Amended by 0010: the byte budget was removed (PO, tl-manages-team); the rest stands.` and change nothing else in it. Contain nothing the scope did not decide. If `CONTEXT.md` does not exist, `promote.md` says what to create; create only the terms listed. If the scope's decisions changed after you started, the Tech Lead updates `promote.md` and you re-read it.

`CONTEXT.md`: also change **Integration task** ("runs the full suite" → runs the targeted tests; the Tech Lead then runs the full suite) and **Receipt** (made by the Tech Lead's one run). ADR 0010 gets the suite consequence listed in `promote.md`.

## Technical AC
AC-7. Business AC: B13.
