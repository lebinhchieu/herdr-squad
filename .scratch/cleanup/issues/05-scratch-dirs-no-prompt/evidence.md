# Evidence 05: scratch dirs without a PO prompt
## Behaviour

**SAFE-11 (new text, 148 B):** ``Scratch dirs: `mktemp -d` only. `cd` out before `rm`. One path per `rm`, no `$`, backtick or `..` (PO prompt): `rm -rf /tmp/tmp.X`; repeat per dir.`` Was 144 B: **+4 B** for dev, qa-whitebox, qa-blackbox (other roles do not get it). Largest composed dev set 5113 -> 5117 B (limit 5120).

**Deviation from the Design-notes text (T1):** the TL's wording (two examples, `D=...; rm -rf "${D:?}"` exception, `cd` reason) is ~330 B and pushed the largest dev set to 5203 B > 5120 (`test_dev_rules_size`, T4). Cut to the form above: one literal example, `&&` chain and `"${D:?}"` form dropped, the `$` ban is absolute. The `&&` chain still passes (run below as `ok2`); the `${D:?}` form is no longer advised. Raising the limit was not mine to do.

**T2** `test_squadsettings.test_safe11_rm_examples_match_allow_and_no_ask`: extracts SAFE-11's backticked `rm` commands, for all six role settings asserts allow-match, no ask-match, no `$`; negative control `rm -rf /tmp/tmp.A /tmp/tmp.B` matches an ask. Green.
**T3** `git diff HEAD --stat -- templates/squad/settings`: empty; `test_scratch_rm_allowed_only_under_mktemp_dirs` unchanged, green.
**T4** `test_dev_rules_size` green with `"${VAR:?}"` needle -> `rm -rf /tmp/tmp.`; golden role rows in `test_team_lead_role` are role reach, unchanged, green.
**T5** changelog `## v10 — 2026-10-28`, `changed: SAFE-11 ... why:`; `bin/squad-process lint` empty rc 0. `upgrade --check` on a pin of the old SAFE-11 (old-root = `git archive 7c41807`, overlay `replace SAFE-11 @591f7227`): `plugin changes: added 0, changed 1`, `SAFE-11 stale ... (@591f7227 -> @07c623d7)`. One test follow-up: `test_team_duties` asserted the changelog *starts* with `## v9`; now asserts it contains it.

**T6 live** `claude -p --model haiku --settings templates/squad/settings/dev.json [--permission-mode auto]`, scratch dirs from `mktemp -d`, from `/`, `permission_denials` counted (script run 10 at once):
| case | command | default | auto |
|---|---|---|---|
| ok1 | `rm -rf /tmp/tmp.A` (SAFE-11 example) | 0 denials, gone | 0, gone |
| ok2 | `rm -rf /tmp/tmp.A && rm -rf /tmp/tmp.B` | 0, both gone | 0, both gone |
| two | `rm -rf /tmp/tmp.A /tmp/tmp.B` | 1, survive | 1, survive |
| dollar | `rm -rf /tmp/tmp.A/"${f:?}"` | 1, survives | 1, survives |
| dots | `rm -rf /tmp/tmp.A/../tmp.B` | 1, survive | 1, survive |

**Tests run:** test_squadsettings, test_dev_rules_size, test_team_lead_role, test_team_duties, test_promotion_0_6_0, test_advisor_rules, test_old_language_inventory, test_sizes, test_squadrules, test_squadscaffold: all OK. Full suite: Tech Lead.
