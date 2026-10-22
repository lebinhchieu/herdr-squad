Status: ready-for-agent
Type: integration
Task ID: 04
Touches: `.scratch/evidence-inline/spec.md` and `issues/01-05` (committed here, first commit: see What 0); merge of the passed branches of 01, 02, 03; `.scratch/evidence-inline/issues/0[1-3]-*.evidence/` (the assembled evidence)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_evidence test_process_history test_instructions test_templates test_windows_safe test_processlint`
Blocked by: 01, 02, 03 passed

# 04: integration and live check

**Done when the three branches merge clean, the targeted tests pass on the merge, and the new tool has assembled the real evidence of 01–03.**

## What
0. First commit on your branch: copy `.scratch/evidence-inline/` (spec.md, issues/) from the project root (absolute path in the briefing) into the same path in your worktree, byte for byte, and commit it (`spec + tickets`). The Tech Lead deletes the root copy after this branch passes. Nothing else of the scope is committed earlier: the ticket files ride this branch.
1. Branch from the scope base, merge the passed branches of 01, 02, 03 (`git merge`, in your own branch only). Resolve nothing silently: a conflict is an `ASK` to the Tech Lead.
2. For each of 01–03, once its `tl-review.md` is in `$SCOPE_DIR/evidence/<NN>/`: run `squad-evidence add <ticket> --heading "Tech Lead review" --from <that file>`, then `squad-evidence check <folder>`.
3. Live check of a screenshot: with `playwright-cli`, take one real screenshot of the rendered `evidence.md` of ticket 01 (serve the folder on 127.0.0.1 with `python3 -m http.server`, stop it by PID), save it as `img/rendered.png` in ticket 04's evidence folder, embed it in ticket 04's `evidence.md` and view the rendered page: the image must show. `squad-evidence check` passes on it.
4. Commit the assembly as one evidence-only commit; `squad-evidence check <folder> --base <merge sha>` passes.

## Technical AC
1. Merge has no conflict (or each is an answered `ASK`); targeted tests pass on the merge sha.
2. `squad-evidence check` exits 0 on all four evidence folders.
3. `git diff --name-only <merge sha> HEAD` lists only `*.evidence/` paths.
4. The screenshot in ticket 04's `evidence.md` is rendered by the page you screenshot (open it and say what you saw).
5. Evidence: ticket 04's own `evidence.md`.
