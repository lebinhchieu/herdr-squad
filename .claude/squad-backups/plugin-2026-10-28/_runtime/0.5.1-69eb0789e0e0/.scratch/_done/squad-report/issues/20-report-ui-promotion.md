Status: ready-for-agent
Type: task
Task ID: 20
Touches: `CONTEXT.md` (squad-report section), `docs/adr/0014-squad-report-derives-from-transcripts.md` (addendum)
Does not touch: code, tests
Harness: none (docs); run `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` is the Tech Lead's job
Blocked by: 19 (commit on the integration branch, last)

# 20: Promotion of report-ui-fix knowledge

**Done when** the wording in `.claude/squads/plugin/scopes/report-ui-fix/promote.md` is committed to the project docs on the integration branch (after 19's passed sha), by the project's rule for editing those files (`/domain-modeling`; glossary terms and ADR 0014 addendum). Business rules → `CONTEXT.md`; technical decisions → ADR 0014 addendum. Use the wording as written; flag any contradiction with an existing ADR line explicitly. One commit, HANDIN 20 to the Tech Lead (docs only; no QA verdict needed beyond Tech Lead check), cc team lead.
