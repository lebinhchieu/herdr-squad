# squad-usage shows only the last session of an agent

Status: needs-triage

Source: upstream-proposals Token Coach (iterations/1.coach.md, Plugin proposals), 2026-11-24.

## Problem
Row `plugin-tech-upstream-proposals` shows peak 61k; `--sessions` shows session 1 at 331k. Second scope (warmcache: 56k shown against 233k). Without `--sessions` the largest overrun of a scope is hidden.

## Proposed fix
Print the largest session peak beside the last one, and say in `--help` what "1st act" and "peak ctx" count.

## Comments
