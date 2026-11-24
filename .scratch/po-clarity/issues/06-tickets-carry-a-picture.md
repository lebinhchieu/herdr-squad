# 06 Tickets carry a picture when it helps

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md`

## Problem

Squad tickets are hard to read. `upstream-proposals` ticket 10 has a Problem paragraph of 7 sentences and a Files paragraph of 6, and no picture of what changes. Chieu has to rebuild the picture in his head.

## Change

1. **Rule for ticket writers** (`lifecycle.md`, new rule next to LC-9; roles: Manager, Tech Lead, BA, Architect): every ticket opens with a picture **when the change has a shape**. Choose the form from the table:

   | The change is… | Picture | Example |
   |---|---|---|
   | A screen or panel | ASCII wireframe in a `text` fence | ticket 04 here |
   | A flow, order, or handoff | `diagram` fence, vertical, at most 44 columns | ticket 01 here |
   | Data in several places | table: item × place | ticket 01 table |
   | Text that changes | before / after block | ticket 03 here |
   | A rule or test fix only | none: one-line Problem | ticket 05 of upstream-proposals |

   The Problem section is at most 3 sentences plus the picture. Put details in Change or AC, not in Problem.

2. **Board renders it.** The ticket view (`panel_files.js` `renderMd`) keeps a fence's spacing (already true, `<pre>`), labels a `diagram` fence with its caption, and shows `![alt](img/x.png)` images from the ticket's evidence folder (same folder rule as `/api/open`; only `.png`/`.jpg`/`.svg`, served under the existing CSP).

3. **Ticket template**: add `templates/squad/ticket.md` with the sections Problem (with picture) / Change / AC / Comments. The rule points to it.

This feature's own tickets (01-05) follow the rule and are its worked examples.

## AC

- AC1: `python3 bin/squad-process lint` exits 0 with the new rule, and the rule attaches to the four roles.
- AC2: on the board, a ticket with a `diagram` fence shows the caption above a `<pre>`. A ticket with `![x](img/a.png)` shows the image. `![x](../../etc/passwd)` shows the alt text only.
- AC3: `grep -rl 'renderMd\|mdBlocks' tests/` hits pass.
- AC4: changelog entry and version bump, together with 02 if both land in one release.

## Comments
