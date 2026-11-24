# 03 SAFE-11: never rm scratch

Status: done
Spec: `.scratch/tmp-scratch/spec.md`
Blocked by: 01, 02
Aim: The scratch rule stops asking agents to run rm
Estimate: 20m
Depends on: 01, 02

## Problem
SAFE-11 tells agents to `rm` their scratch with a literal path, and recommends `rm -rf "$D"`, which the built-in check blocks.

Before: "`rm` there takes only a literal absolute path: `rm /tmp/<dir>/<file>`, or `rm -rf "$D"` after `D=$(mktemp -d)`."
After: "Scratch goes in your scratch dir `$TMPDIR` (`mktemp -d` lands there). Never `rm` it: `squad-retire` deletes it."

## Change
SAFE-11 and SAFE-11b in `templates/squad/process/safety.md`; changelog v32; tests that pin the wording.

## AC
- AC1: SAFE-11 names `$TMPDIR`, says never to `rm` scratch, and names `squad-tmp rm` for mid-task cleanup.
- AC2: no rule recommends an `rm` with a `$` target.

## Comments
