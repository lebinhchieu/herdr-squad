# 05 Role settings drop the rtk rewrite hook

Status: done
Spec: `.scratch/tmp-scratch/spec.md`
Blocked by: none
Aim: Auto mode can judge every command an agent runs
Estimate: 20m
Depends on: none

## Problem
`squad-spawn` merges the user's hooks into each role's settings, including `rtk hook claude`, which rewrites a Bash command after auto mode reviewed it; auto mode then gives no verdict and the call prompts (332 times in 10 days).

## Change
The lean settings merge in `squad-spawn` drops every hook whose command starts with `rtk hook`, and a matcher group left empty. Other user hooks stay.

## AC
- AC1: a role's merged settings hold no `rtk hook` command; the user's other hooks are kept.

## Comments
