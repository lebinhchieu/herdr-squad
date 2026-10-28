INT4 964c443 (merge 3c931a9): diff 3c931a9..964c443 = ticket file + evidence.md only (same shape as INT3); squad-evidence check flags only the new ticket .md (known shape). Suite --if-changed 90be196 running -> evidence/INT4.
964c443 suite FAIL 1/1667: test_team_lead_perms TL_ALLOW stale from 14 (Dev missed grep hit). INT4 returned; rerun suite on new sha. Lesson: 14's grep -rl of settings/ missed team-lead perms test.
final e265fd7 (code), evidence 2175bd2: suite --if-changed 90be196 OK 1667 clean=yes (evidence/INT4/suite-default.txt); evidence check exit 0. Tech accept.
INT4 evidence 17b88b9 (evidence-only on e265fd7, check exit 0). DONE; integration sha for 12 = 17b88b9.
