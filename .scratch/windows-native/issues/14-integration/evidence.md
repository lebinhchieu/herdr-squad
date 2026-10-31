# 14-integration evidence

## Behaviour

**Unrun.** PO order: no test was run. Static checks only.

Branch `squad/plugin/solve-windows/plugin-dev-solve-windows-21`. Start `018df30` (14i, on 14c `7f9e40f`, on 14a `73dba68`). 14b is not included (held, branch -16).

| Merge | Source | Final sha | Merge commit |
|---|---|---|---|
| 1 | plugin-dev-solve-windows-15 (14g, base `4a8ed47`) | `0c1c2cb` | `d082f79` |
| 2 | plugin-dev-solve-windows-20 (14h, run_suite.py only) | `e2ffb1e` | `34f56bf` |

Both used `git merge --no-ff`. No conflict.

| Check | Seen |
|---|---|
| Diff vs each branch's own diff | `git diff --name-status` of `4a8ed47..0c1c2cb` and `73dba68..e2ffb1e` equals the same files in the merge results. The merges add nothing else. |
| Deleted files not referenced | The 11 files from 14g (advisor_rules, designer_handoff, manager_inbox_read, manager_m_l, pod_contact_routes, pod_rules_process, process_citations, retro_rules, suite_rules_process, task_id_rule, team_lead_role): `git grep` of each module name finds no code or doc reference. Only old `.scratch` evidence notes mention them, plus two new test names that contain `task_id_rule` (`test_rules_contract.py:47`, `test_rules_wording.py:96`). |
| Compile, no write | `compile()` of `tests/rulesview.py`, `run_suite.py`, `test_rules_contract.py`, `test_rules_wording.py`: ok. |
| `def test_` counts | 14g: the 11 deleted files had 31 at `4a8ed47`; now `test_rules_contract` 13 + `test_rules_wording` 17 = 30, as the 14g evidence says. 14a: runtime 68, settings 24, scaffold 5, squad_label 14, as in the 14a table. 14i: team_duties 20, dev_rules_size 9, qab_optional 11, as in the 14i evidence. |

## Review

Fresh-context review (sonnet, high) of `018df30..HEAD`: no findings. Merges add nothing beyond their branches, deleted files are unreferenced outside `.scratch`, all four files parse.
