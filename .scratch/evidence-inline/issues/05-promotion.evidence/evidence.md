# Evidence: 05 promotion
sha: 84b76b838ad3e26ad17f719da461231eec1b493c

## Behaviour

No UI: no screenshots. Command output below, run on 84b76b838ad3e26ad17f719da461231eec1b493c.

### AC 1: ADR text and glossary entries are exactly those in promote.md

```
$ python3 (compare docs/adr/0015-evidence-next-to-the-ticket.md with the fenced ADR block of promote.md)
ADR identical to promote.md block: True

$ git diff HEAD~1 HEAD -- CONTEXT.md
+**Evidence folder**:
+The folder `<ticket path minus .md>.evidence/` next to a ticket, holding `evidence.md` (the one file the PO reads) and `img/`. The reviewers' working files (`qa-w.md`, `qa-b.md`, `tl-review.md`) and suite receipts stay in `$SCOPE_DIR/evidence/<task>/`.
+_Avoid_: evidence dir, proof folder
+
+**Evidence sha**:
+The commit where the Developer assembled the reviewers' files into `evidence.md` after every checker passed; its diff to the passed sha touches only evidence folders, and the Manager may merge it as the passed sha.
```

Both entries sit in the Work section, after the existing "Evidence" entry, in the file's format (bold term, definition, _Avoid_ line). The working-files note is folded into the Evidence folder entry, as promote.md says.

### AC 2: only the two files; tests

```
$ git diff --stat HEAD~1 HEAD      (HEAD = 84b76b8)
 CONTEXT.md                                   |  7 +++++++
 docs/adr/0015-evidence-next-to-the-ticket.md | 11 +++++++++++
 2 files changed, 18 insertions(+)

$ cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_history test_instructions
Ran 33 tests in 0.057s
OK
```
