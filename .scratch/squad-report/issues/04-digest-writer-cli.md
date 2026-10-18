Status: ready-for-agent
Type: task
Task ID: 04
Touches: `bin/squad-report` (new, executable), `bin/squadreport_build.py` (new), `bin/squadreport_digest.py` (new), `bin/squadreport_embed.py` (new), `bin/squadreport_rollup.py` (stub: `run(argv)` printing "not built" exit 2), `bin/squadreport_query.py` (stub, same), `tests/test_squadreport_digest.py`, `tests/test_squad_report_cli.py`, `tests/test_squadreport_embed.py` (all new)
Does not touch: `bin/squadreport.py`, `bin/squadreport_tasks.py` (read only), `templates/report/*` other than reading `config.json`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadreport_digest test_squad_report_cli test_squadreport_embed test_squadreport_collect test_squadreport_tasks test_windows_safe`. CLI tests follow `test_squad_inbox` style (subprocess against a scratch squad built by `report_fixtures`).
Blocked by: 03

# 04: Digest, `data.json` writer, CLI `squad-report <scope>` and `status`

**Done when `squad-report <scope>` writes `report/data.json` (deterministic) and prints the path and 5-line summary.** Freezes schema v1. Business AC1.1-1.2 (data side), 1.5, 1.6, 7.1, 7.3, 7.4, 9.1-9.3; spec → Technical → "CLI", "Digest".

## What
- `bin/squad-report` is thin and **owns the subcommand table for everyone**: `<scope|goal>`, `rollup`, `query`, `status` dispatch to `squadreport_build.run`, `squadreport_rollup.run(argv)`, `squadreport_query.run(argv)`; 06 and 07 fill their module and never edit this file. Flags: `--squad --out --no-html --quiet --final --redact --deadline N`. Exit codes per spec (0 ok, 1 error, 2 refusal, 3/4 for `status` stale/missing, 5 deadline). Names resolve against `scopes/`, `scopes/_done/`, `goals/`, `goals/_done/`. `--no-html` skips rendering; the render step lazily imports `squadreport_html.render_scope(data, out_dir)` and is skipped when that module does not exist yet (before 05), so 05 never edits 04's files.
- `squadreport_build.build(...)`: `collect` -> `base_data` -> `fill` -> `digest` -> `generated_at`, `partial` (running unless `--final`) -> `data.json` written to a temp name in the same folder then `os.replace`; `sort_keys`, separators `(",",":")`, `utf-8`, `newline="\n"`.
- `squadreport_digest.digest(data) -> list`: the 12 kinds in the spec, max 8, ranked by `weight` desc, ties by the spec's kind order; `text` is built from numbers by a template; thresholds only 3 returns and 60% attributed. Same input, same digest.
- `squadreport_embed.py` (used read-only by 05 and 06): `plugin_assets()` (assets from `dirname(realpath(__file__))/../templates/report`, never the squad), `json_for_script(obj)` (escape `<`, `>`, `&`, U+2028/9 as `\uXXXX`), `assemble(template, css, js, data)` (replaces `__CSS__ __JS__ __DATA__`, one file), `atomic_write(path, text)`.

## Technical AC
1. Two runs on equal input: `data.json` bytes equal except `generated_at`; no duplicate rows (AC1.5, AC9.3). Running a built `_done` scope writes only its new `report/`.
2. Output: first line the path of `report.html` (or `data.json` with `--no-html`), then 5 lines: elapsed, agent-time, est. cost, returns, % attributed; ASCII only, no ANSI; `--quiet` prints nothing on success.
3. No LLM and no network: the test runs the CLI with a `claude` stub on PATH that fails the test if invoked, and with sockets blocked (monkeypatch `socket.socket` in-process for `build`).
4. `status`: `fresh` exit 0 | `stale` 3 (a message, escalation or roster row newer than `data.json`'s `sources`) | `missing` 4.
5. Refusals exit 2 with a one-line message: flat squad, unknown name, a scope whose transcripts are all gone (existing `data.json` untouched); `--deadline` exceeded exits 5 and leaves the old `data.json`.
6. `json_for_script` plant: `</script><img src=x onerror=1>` and U+2028 inside a title round-trip through `json.loads` and never contain a raw `</script`/`<` in the embedded text. `assemble` output has no `http://` / `https://` URL.
7. `digest`: hand-computed fixture gives the expected ranked list; with >8 candidates 8 are kept; `attribution_low` appears only below 60%.
8. A test pins the message type list the digest knows (ASK, BLOCKED, HANDIN, PASS, FAIL, ANSWER, DECISION, STATUS) against the regex in `bin/squad-log-message` (risk "process drift").
9. **Field shape on the full build output** (not hand-built dicts): every `tasks[]`, `returns_list[]`, `iterations[]`, `matrix[]`, `roles[]`, `agents[]` and `digest[]` row has every field the spec lists and no others; every `segments` row has exactly 5 elements, `start <= end`, bucket in `w|a|b|i`; every closed item has its end. The test builds the 02/03 fixture scope through `squadreport_build.build` and checks the result.
10. Goal-name resolution: `squad-report <goal>` resolves against `goals/` and `goals/_done/` and calls the rollup entry (`squadreport_rollup.run`, still the stub here: exit 2 "not built" is accepted until 06); an unknown name exits 2.
11. **Real-data check (process.md → Verify against the real thing), QA whitebox, once, read-only:** `squad-report` on a copy of `_done/win-compat` and `_done/remove-board` into a temp `--out`; assert the invariants, returns == FAIL dedup count (6 / 1), PO wait items == the escalations, every row has the fields the consumer reads, the % attributed (non-idle) figure and `cost_delta_pct` reported, and the constant/idle case (a scope with one agent and no messages). Result saved in `evidence/04/real-data.md`; the numbers feed the digest threshold decision.
12. Primary behaviour only (qa: light).
