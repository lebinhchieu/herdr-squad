# Evidence: 04 ADR 0026: pane lists every home

## QA whitebox

### QA whitebox: ticket 04 (ADR 0026), sha b5963eb

Verdict: PASS. Checked read-only with git on the commit (no checkout).

| AC (tech-ac T4) | Result | How |
|---|---|---|
| ADR 0026 equals `tasks/adr-0026-draft.md`, Status accepted | ok | `git show b5963eb:docs/adr/0026-*.md` diffed to the draft: identical; line 3 `Status: accepted (...)` |
| 0007 exactly one changed line | ok | `git diff --numstat`: 1/1, line 11, pointer "(amended by 0026 ...)" added at the end; no other line |
| 0020 exactly one changed line | ok | numstat 1/1, line 12, same pointer |
| no other file | ok | `--stat`: 3 files only |
No code or printed text changed: SQ-10 and test runs do not apply.

#### Follow-ups (not AC, not a return, SQ-4)
1. ADR 0026 line 3 keeps the draft's meta text: "Draft text for `docs/adr/0026-...`, written by a Developer in the promotion task once accepted." It reads wrong in a final ADR. The AC says "matches the draft", so left as is; Tech Lead may trim it in ticket 06.
2. ADR 0026 line 5 says it amends 0020's "no cross-squad view" too (0020 line 7), but only line 12 carries the pointer. Ticket says one line each; the Developer asked. Tech Lead to decide.

## QA blackbox

### QA blackbox: ticket 04 (ADR 0026), sha b5963eb

Docs-only ticket: no running behaviour. AC from plan.md: "ADR text per Tech Lead draft, accepted by Chieu".

| AC | shot/live | What I did | What I saw | Result |
|---|---|---|---|---|
| ADR 0026 text equals `tasks/adr-0026-draft.md` | live | `diff` of `git show b5963eb:docs/adr/0026-squads-pane-lists-every-home.md` with the draft | no difference | pass |
| `Status: accepted` | live | read the file's Status line | "Status: accepted (squads-mod; Chieu answered E2 (a) ...)" | pass |
| One line each in 0007 and 0020 point to 0026 | live | `git diff --numstat`; read the changed lines | 1/1 on 0007 (line 11) and 0020 (line 12); 0026 new (19/0); each line ends "(amended by 0026: the `/squads` pane lists every home, list-only...)" | pass |
| Copy-only decision recorded (Chieu) | live | read Decision paragraph | "It runs no command at all ... copied on a click (Chieu's choice, copy only)" | pass |

Follow-ups (not AC misses):
1. ADR 0026 first paragraph still says "Draft text for ... written by a Developer in the promotion task once accepted" and "six row facts" while it lists five (spec now says name plus five facts). Both copy the draft.
2. 0020 line 7 still says "no cross-squad view" (Developer left it on purpose).
