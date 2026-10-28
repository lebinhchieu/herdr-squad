# Squad

## Haiku Extractor

## Agents should minimize output in chat to reduce output token

## Issues

### Issue: Respawn should not trigger after spawning sub agents

Look like it becomes idle while waiting for the subagent -> exceeded context windows limit -> respawn -> the subagent is killed (issue)
I believe it should stay there instead of respawn
My case: I ask dev to use /implement (mattpocock skill). It done the code change, spawn subagent to review (code-review skill), then respawn right after that.
