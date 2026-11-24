# Evidence 11 worktree reuse (SPAWN-5a/5b) and branch wording

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 SPAWN-5a reuse text, 2 added lines | `git diff templates/squad/process/spawning.md` | read the diff |
| AC2 SPAWN-5b same text | same diff; wording differs slightly because the rule lint refuses a repeated sentence | `test_rules_wording.CitationsTest.test_lint_resolves_every_pointer` |
| AC3 `squad-spawn --worktree` accepts a dev role | dry-run output below | `squad-spawn dev plugin-dev-x-2 --squad plugin --scope suite-worktree --repo . --worktree <wt> --dry-run` |
| AC4 branch wording | `grep -rn 'squad/<squad>' templates/` below | files: starting.md (START-10), review.md (5 HANDIN lines), safety.md (SAFE-1a) |
| AC5 touched tests + grep hits pass | test list below | `cd tests && python3 -m unittest <names>` |

## Behaviour

- AC3: the dry-run prints `would run: herdr tab create --cwd <previous worktree> ...` and an `agent start ... --name plugin-dev-x-2` line, exit 0. No `git worktree add`, so no new branch. Source: `bin/squad-spawn` lines 24-25 (usage), 68 (parse), 276-279 (`--worktree` sets cwd; `--base` with it is refused).
- AC4: after the edit `grep -rn 'squad/<squad>' templates/` hits only spawning.md:55 (first spawn creates a new worktree, correct as is). START-10 now says "Work only on the branch of your worktree (`git branch --show-current`)"; HANDIN lines say "the branch of your worktree (`git branch --show-current`)"; SAFE-1a says "Commit only to the branch of your worktree (`git branch --show-current`)".
- Side effect: composed Manager rules grew 291 B (SPAWN-5a), so the pinned byte budgets in `tests/test_dev_rules_size.py` went up by 291 (comment says why). The HANDIN needle in the same test now quotes the new wording.
- AC5: `grep -rl` over tests/ for the changed strings hit only `test_dev_rules_size.py` (edited). Ran: test_dev_rules_size, test_rules_wording, test_rules_contract, test_sizes, test_squadrules, test_squad_spawn, test_qab_optional: 195 tests, 1 failure. The failure is `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file`; it fails the same way on a `git archive HEAD` copy of the base (also noted in evidence 09), so it is not from this ticket.
- Not changed: `bin/squadboard_active.py` and `bin/squad-spawn` still assume branch `squad/<squad>/<scope>/<agent>` per agent name (board shows tips per branch). A reused worktree shows under the old agent's name. Outside Files:; follow-up for the Manager.
