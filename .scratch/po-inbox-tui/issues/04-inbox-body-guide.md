# Task 04: Manager inbox-body writing guide

Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=dev, business-ac=ticket, code-check=dev (self-review, Manager confirms), behaviour-check=dev evidence (Manager confirms), handin-target=manager, suite-owner=qa-white (at the end only), promote-owner=dev, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Team: no QA (PO decision 2026-10-29). Branch from the passed sha of task 03. Cite [PROMO-5] (promotion): commit `promote.md` into the project docs. Hand in to the Manager. `BLOCKED 04` on a risk flag or doubt. Cite [PROMO-5] (promotion): commit `promote.md` into the project docs.
Goal: scope brief `../scope.md`, plan `../iterations/1.md`. Spec: `.scratch/po-inbox-tui/spec.md`.
Design: ui-design/body-styles.md (section 6, the guide)
Depends: 03 (the guide's examples must draw as written).

## What
Commit the Manager's writing guide (design section 6) as `docs/inbox-body-guide.md` in the repo, with its two example bodies. The role-instruction change (`agents/manager.md`: one pointer line to the guide) is NOT part of this task: the Manager drafts it in `iterations/1.md` for the PO to approve (WHO-6). If a rule must bind teammates without the squad, add it to the project instructions file (`CLAUDE.md`) here, one short rule at most.

## Touches (confirmed before AC)
`docs/inbox-body-guide.md` (new); a test that parses both example bodies of the guide with the real parser and checks the block types the guide states (extend `markup.test.ts` fixtures from 03); `CLAUDE.md` only if a rule is added. Not touched: `agents/*.md`, `hooks/po-inbox/*.tsx`.

## AC
1. The guide states: verdict first (callout), then a table of options, then a diagram or list, prose only for one reason line; each rule with a one-line why.
2. Both examples in the guide are the fixtures from task 03; the test fails if a form stops parsing as the guide says.
3. Every form named in the guide exists in the pane (03 landed): no advice for a form the pane cannot draw.
4. English plain, short sentences (the PO is a non-native reader).
5. Evidence: `issues/04-inbox-body-guide/evidence.md` with the guide path, sha and the test run. Targeted tests green.

## Design notes
(Developer writes here before building.)

## Verification (no QA)
Before HANDIN: (1) run the `mattpocock-skills:code-review` skill on your branch since its base and fix every finding it confirms; (2) write `## Review` in this file: findings, what you fixed, what you left and why; (3) run only the test files you touched plus the `grep -rl` hits (CLAUDE.md); do NOT run the full suite (PO: full suite only once, at the end, by QA whitebox on the final integrated sha); (4) save real-pane evidence per the AC in `evidence.md` and check it with `squad-evidence check`. HANDIN names the branch, sha, evidence sha and the `## Review` path. The Manager confirms; no QA runs.
