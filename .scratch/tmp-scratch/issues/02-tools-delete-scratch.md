# 02 squad-retire and squad-close delete the scratch dir

Status: done
Spec: `.scratch/tmp-scratch/spec.md`
Blocked by: 01
Aim: Scratch is deleted by tools, never by an agent
Estimate: 30m
Depends on: 01

## Problem
With scratch in a per-agent dir, someone still has to delete it; an agent's `rm` is what prompts.

## Change
- `squad-tmp clean <agent>`: deletes `<root>/<agent>` in Python; the name must be a plain token, the target must sit directly under the root.
- `squad-retire` runs it after the pane closes (a failure only warns). `squad-close` reaches it through `squad-retire`, and cleans the dir of an agent that was not live too. `squad-respawn` keeps it.

## AC
- AC1: after `squad-retire <agent>` the agent's scratch dir is gone.
- AC2: `squad-tmp clean ../x`, `clean ''` and `clean .` are refused with exit 2 and delete nothing.

## Comments
