# plugin-dev-dsz-14 notes
- Ticket 14 done: final b2ee4e5, evidence 7c8af4a, both QAs PASS. Nothing open.
- rm allow `/tmp/tmp.*` needs paired asks (`* *`, `*..*`, `*$*`, backtick): `*` matches spaces, `..`, `$()`. Globs refused by Claude itself (known gap).
- Left in /tmp from live tests (not removed): /tmp/zz-victim-t14, /tmp/t14.scratch and the dir it names, /tmp/tmp.75TXUpd2o8, /tmp/other-t14.
