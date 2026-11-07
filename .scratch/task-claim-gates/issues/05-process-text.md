# 05 Process text and version bump

Status: ready-for-agent
Blocked by: 02, 03, 06

templates/squad/process: no confirmer (passed when every QA PASSed), no-QA path by `squad-evidence check` at HANDIN, merged, warn gates, `squad-task` manual command; version bump (SQ-5).

Files: templates/squad/process/* (core, who, teams, sizes, lifecycle, review, merge, spawning, starting), .claude-plugin/plugin.json (0.7.5 -> 0.7.6; `grep -rn 0.7.5` finds no other pin), tests/test_rules_wording.py, tests/test_dev_rules_size.py (Manager byte baselines)
AC: text matches states.md s4, s6.
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.
