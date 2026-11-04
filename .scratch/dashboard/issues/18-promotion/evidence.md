# Evidence 18 promotion

## Behaviour
Doc-only. `README.md` row for `bin/squad-board` replaced by the text of `promote.md` section 1, as one table row. `git diff --stat main`-style check: only `README.md` changed in this commit.
- Checked against code: `squad-board --help` lists `--squad NAME|PATH`, `--goal G`, `--scope S`, `--port N` (default 8765; 0 picks a free one), `--herdr-json FILE`, `--no-open`. `--goal` with `--scope` is refused ("cannot be used together"). `squad-inbox park` takes `--text --from --blocks --level {scope,goal,squad}`; `unpark` and `resolve --answer` exist.
