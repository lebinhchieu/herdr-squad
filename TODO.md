# Squad

## Haiku Extractor

## Manager Rules

### Always think about reducing working time, optimizing process, optimizing token consuming and ensuring quality

- Balance the quality & cost (time, token). Know that which parts are needed to focus, which parts are lower
- Debate with me (PO) for the best approach
- Instructions, context, shared files that are read is also a cost -> need to consider to have reasonable contents

## Issues

### Issue: Respawn should not trigger after spawning sub agents

Look like it becomes idle while waiting for the subagent -> exceeded context windows limit -> respawn -> the subagent is killed (issue)
I believe it should stay there instead of respawn
My case: I ask dev to use /implement (mattpocock skill). It done the code change, spawn subagent to review (code-review skill), then respawn right after that.
