| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squadboard_panels T07_AC1…: spacing, caption, no bar for bash: OK; img/preview.png | | |
| AC2 | same test: 2 image requests, 4 refused paths alt only: OK | | |
| AC3 | test_squadboard_server T07_AC3: outside base 403, symlink 403, .txt 400, svg sandbox, no img=1 text/html: OK | | |
| AC4 | same panel test: script in alt shown as text, `__x` undefined: OK | | |
| AC5 | same panel test: row click sends no /api/file, Preview sends one: OK | | |
| AC6 | T07_states (loading, err, empty, Esc focus) + img/preview.png | | |
| AC7 | 7 test files listed in Behaviour: OK | | |
| AC8 | img/preview.png (diagram, image, refused image in one shot) | | |
