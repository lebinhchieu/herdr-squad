# Evidence: 07 Plugin version patch bump
## Behaviour
- `.claude-plugin/plugin.json` version 0.6.0 -> 0.6.1. marketplace.json has no version; changelog not touched (the 0.5.2 bump added none).
- `grep -rn '0\.6\.0'` outside .scratch/squads/backups/adr: other hits are release-threshold comments in bin/ and tests, changelog/README text of the 0.6.0 release, fixtures; none is "current version".
- Only pin of the current version: `tests/test_promotion_0_6_0.py` asserted plugin.json == 0.6.0; now asserts >= 0.6.0 (changelog/README checks stay on the 0.6.0 release text).
- Tests passing (unittest, 247): test_promotion_0_6_0, test_squadsettings, test_squadruntime, test_squad_start, test_squad_respawn, test_squad_spawn.
