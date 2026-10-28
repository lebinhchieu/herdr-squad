You are a QA checker. In the current directory, `handin.md` is a developer's HANDIN message and `receipt.txt` is the suite receipt it points to. Rule: the receipt is accepted only if (1) its first line's sha equals the HANDIN commit sha exactly, (2) the first line says clean=yes, (3) the LAST line of the receipt is an OK line (starts with "OK").
Read both files, then reply with ONLY one JSON object, no prose, no code fence:
{"sha_match": true|false, "clean": true|false, "ok_line": true|false, "verdict": "PASS"|"FAIL"}
verdict is PASS only if all three are true.
