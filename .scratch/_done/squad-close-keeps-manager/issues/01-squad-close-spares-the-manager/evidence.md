# 01 evidence

## Behaviour
`squad-close --scope S` / `--goal G` no longer retire the Manager: `== manager` prints `kept <mgr> (Manager stays; squad-retire <mgr> ends it)`; the closing home's pinned runtime is protected (`kept <pin> (<mgr> still runs from it; the next scope or squad close prunes it)`). Whole-squad close retires all Managers last and prunes all runtimes. Pin shared with another holder, or no Manager in roster (scope inside a goal): prune as before.

### Dry-run, scope sc1 (real script, scratch squad)
```
== agents
would retire t-dev-sc1-1
== runtimes
kept 1.0-aaaaaaaaaaaa (t-mgr-sc1 still runs from it; the next scope or squad close prunes it)
kept 1.0-aaaaaaaaaaaa (running)
kept 1.0-bbbbbbbbbbbb (held by scope sc2)
would remove 1.0-cccccccccccc (1.0 MB)
== folder
would move .../scopes/sc1 to .../scopes/_done/sc1
== manager
kept t-mgr-sc1 (Manager stays; squad-retire t-mgr-sc1 ends it)
```
### Dry-run, goal g1
```
== runtimes
kept 1.0-cccccccccccc (t-mgr-g1 still runs from it; the next scope or squad close prunes it)
kept 1.0-aaaaaaaaaaaa (held by scope sc1)
would remove 1.0-bbbbbbbbbbbb (1.0 MB)
== manager
kept t-mgr-g1 (Manager stays; squad-retire t-mgr-g1 ends it)
```
### Dry-run, whole squad
```
== runtimes
would remove 1.0-aaaaaaaaaaaa / bbbb / cccc ... would free 3.0 MB in 3 runtimes
== manager
would retire t-mgr-sc1
would retire t-mgr-g1
```
## Tests
`python3 -m unittest tests.test_squad_close`: 70 OK. Red first: the same tests against HEAD's `bin/squad-close`: 14 failures. `bash -n bin/squad-close` OK.
