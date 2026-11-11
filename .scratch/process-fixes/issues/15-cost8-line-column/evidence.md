# Evidence 15 COST-8 says the Manager reads the line column

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 COST-8 names the `line` column, acts when `last ctx` passes it; at most 2 added lines; other sentences kept | `git diff templates/squad/process/cost.md`: 1 added paragraph (2 lines with the blank), no removed line | `git diff templates/squad/process/cost.md` |
| AC2 lint and quoting tests pass | lint rc 0; test files below | `python3 bin/squad-process lint`; `cd tests && python3 -m unittest <names>` |

## Behaviour

- AC1: the added paragraph: "The hook does not watch the Manager between those calls. Read the `line` column of your `squad-usage` row: when `last ctx` is past it, write notes and run `squad-respawn`." No number in it. The diff has only additions; COST-8b is untouched.
- T6, composed rule (`python3 bin/squad-process rule COST-8` from the worktree) ends with that paragraph after the original one. (The `squad-process` on PATH is the pinned plugin, so it still shows the old text.)
- AC2: `python3 bin/squad-process lint` rc 0. Ran every `tests/` file that names `cost.md` or `COST-`: test_rules_wording 29, test_squad_manager_guard 25, test_squad_usage_hook 10, test_dev_rules_size 9, test_sizes 8, test_rules_contract 14; also test_instructions 16 and test_templates 7. All OK. Full suite not run.
