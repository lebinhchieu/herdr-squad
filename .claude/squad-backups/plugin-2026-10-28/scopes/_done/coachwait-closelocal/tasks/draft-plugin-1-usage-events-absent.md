# Draft: usage-events.jsonl may not exist; Coach card should say so
START-17/ITER-7 tell the Token Coach to read `usage-events.jsonl`; in this scope the file never existed (0 expiries/compactions). Either the hook creates it only on an event (then say "absent = no events" in the rule/card) or it is not created. Evidence: iterations/1.coach.md, Plugin proposals 1.
