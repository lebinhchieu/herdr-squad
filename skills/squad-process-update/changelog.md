## v9 — 2026-10-27
Teams replace sizes (drop-scope-size, 0.6.0). Each rule-file task appends its changed IDs under the headings below; the snapshot line and the final text come with the promotion task.

added:
- TEAM-1: Done when QA whitebox is the only QA (`qa-white = yes and qa-black = no`)
- TEAM-2: Done when QA blackbox is the only QA
- TEAM-3: Done with no QA on the team: the Developer's evidence confirmed by the code-check owner
- TEAM-4: QA whitebox checks the Developer's `## Behaviour` when no QA blackbox is on the team
- TEAM-5: the BA owns the business AC alone when no QA blackbox is on the team
- TEAM-6: the Tech Lead confirms the Developer's `## Review` when no QA whitebox is on the team
- TEAM-7: removing a role (iteration boundary, PO's OK, Handover names the new owner)

changed:
- SIZE-1: now the team proposal table (a row for every role), signals and risk flags; was the size proposal. Body rewritten, ID kept because starting.md cites it
- SIZE-2: now Done = every checker, both QAs variant (`qa-white = yes and qa-black = yes`); was the table of three sizes. ID kept: starting, lifecycle and spawning cite it
- SIZE-5a: business AC are the ticket when `business-ac = ticket`; the move-to-L sentence is now add the BA
- SIZE-5c: acts for QA blackbox only (`business-ac = ticket and qa-black = yes`); the Manager part moved to SIZE-5a so no absent role acts
- SIZE-6c: one Developer-duties rule for `plan-owner = manager`, copying the `duties:` header line; was the S variant of two twins
- SIZE-11a: when `doubt-owner = manager`; the scope moves to L is now add the BA
- SIZE-13: now adding a role by late signal; was moving a scope up a size. ID kept: review.md and who.md cite it
- SIZE-14: now a late signal found while building, add the role; was a behaviour change in S. ID kept: messages.md cites it
- SIZE-16: Handover on adding a role; wording only, no size
- SIZE-17a: joining a scope already under way; composes only with its own role on the team (`<role> = yes`), wording without size
- SIZE-17b: joining a scope already under way; composes only with its own role on the team (`<role> = yes`), wording without size
- SIZE-17c: joining a scope already under way; composes only with its own role on the team (`<role> = yes`), wording without size
- SIZE-17d: joining a scope already under way; composes only with its own role on the team (`<role> = yes`), wording without size
- SIZE-17e: joining a scope already under way; composes only with its own role on the team (`<role> = yes`), wording without size
- SIZE-23c: QA whitebox checks the diff against `architecture.md` whenever it is on the team (`qa-white = yes and architecture = yes`); adds it to the AC when it owns it
- SIZE-23d: acts for the Tech Lead only (`tech-ac = tech-lead and architecture = yes`); QA whitebox's check moved to SIZE-23c so no absent role acts
- SIZE-18: extra hands when `plan-owner = team-lead`
- SIZE-21a: now spawning the confirmed team (every team); was spawn without QA blackbox at M. ID kept: history snapshots cite it
- SIZE-22: now the duty owner chain table by team; was the table by size. ID kept: promotion.md cites it
- SIZE-9: dropped the words in every size; the duty is unchanged
- SIZE-9a: dropped the words in every size; the duty is unchanged
- SIZE-10a: wording only, no size
- SIZE-10b: wording only, no size
- SIZE-11b: the BA tells the plan owner instead of the Team Lead, so no absent role is named
- MSG-6: `plan-owner = team-lead`; the size-change signal is a signal to add a role. ID kept: MSG-13 cites it
- MSG-11a: `plan-owner = manager`; a business doubt changes the team, no BA named. ID kept: Developers' on-demand pointers cite it
- MSG-11b: `plan-owner = team-lead`; asks the owner roster.md names, else the Team Lead, so no absent Tech Lead or BA is named
- MSG-12: `doubt-owner = ba`; takes gaps from the plan owner, not the Team Lead by name
- MSG-13: `plan-owner = team-lead`; raises gaps to the owner roster.md names, so no absent BA or Tech Lead is named
- MSG-16a: `doubt-owner = manager and design = yes`; a business doubt changes the team ([SIZE-14]), no move to L
- MSG-16b: `doubt-owner = ba and design = yes`; a feasibility doubt goes to the owner roster.md names, no absent Tech Lead named
- MSG-20a: `doubt-owner = manager and architecture = yes`; the Manager changes the team ([SIZE-14]), no move to L
- MSG-20b: `doubt-owner = ba and architecture = yes`; feasibility to the owner roster.md names; final goes to the Team Lead only if the team has one
- SPAWN-2a: `plan-owner = manager`; spawns dev and every role on `team:`; was the S list. ID kept: spawning.md and SPAWN-4a cite it
- SPAWN-2b: `plan-owner = team-lead`; the Manager spawns the Team Lead and every role on `team:`; was the M list. ID kept: SPAWN-4a cites it
- SPAWN-2c: `plan-owner = team-lead`; only the sentence that the Team Lead spawns Developers; was the L list. ID kept: SPAWN-4a cites it
- SPAWN-3: the team, not the size, goes in the first prompt; ID kept: SPAWN-2 cites it
- SPAWN-4: the Designer is spawned when `designer` is on `team:`, not by reading `design: yes`
- SPAWN-4a: the Architect is spawned when `architect` is on `team:`; cites SPAWN-2a and SPAWN-2c; no S, M, L words

removed:
- SIZE-3: the Manager proposes the Designer from signals; replaced by SIZE-1
- SIZE-3a: the Manager proposes the Architect from signals; replaced by SIZE-1
- SIZE-4: signals and risk flags fold into the team proposal; replaced by SIZE-1
- SIZE-6d: twin of SIZE-6c; replaced by SIZE-6c
- SIZE-12: duties of a missing role are the duty owner chains; replaced by SIZE-22
- SIZE-15: moving down is removing a role; replaced by TEAM-7
- SIZE-19: QA blackbox off is a non-pick of the proposal; replaced by SIZE-1
- SIZE-20: Done without QA blackbox is a Done variant; replaced by TEAM-1
- SIZE-21b: twin of SIZE-21a; replaced by SIZE-21a
- SIZE-22a: Architect rows fold into the chain table; replaced by SIZE-22

retargeted:
- SIZE-5b: `when: business-ac = ba and qa-black = yes` (was size = L and qa-b = yes)
- SIZE-6a: `when: plan-owner = manager` (was size in S, M)
- SIZE-6b: `when: plan-owner = team-lead` (was size = L)
- SIZE-7a: `when: code-check = manager` (was size = S)
- SIZE-7b: `when: code-check = qa-white` (was size in M, L)
- SIZE-8a: `when: behaviour-check = manager` (was size = S)
- SIZE-8b: `when: behaviour-check = qa-black` (was size in M, L and qa-b = yes)
- SIZE-10a: `when: ui-check = manager and design = yes` (was size = S and design = yes)
- SIZE-10b: `when: ui-check = qa-black and design = yes` (was size in M, L and design = yes)
- SIZE-23b: `when: tech-ac = qa-white` (was size = M)
- SIZE-24b: `when: promote-owner = qa-white` (was size = M)
- MSG-4a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- MSG-4b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-5: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-7a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- MSG-7b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-8a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- MSG-8b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-14: `when: tech-lead = yes` (was size = L); roles unchanged
- MSG-15: `when: ba = yes` (was size = L); roles unchanged
- MSG-17: `when: design-notes = tech-lead and design = yes` (was size = L and design = yes); roles unchanged
- MSG-17b: `when: design-notes = dev and design = yes` (was size in S, M and design = yes); roles unchanged
- MSG-18: `when: plan-owner = manager` (was size in S, M); roles unchanged
- MSG-19: `when: plan-owner = team-lead` (was size = L); roles unchanged
- COST-4a: `when: tech-lead = yes` (was size = L); roles unchanged
- COST-4b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- COST-5: `when: plan-owner = team-lead` (was size = L); roles unchanged
- COST-5a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- COST-6a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- COST-6b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- COST-10a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- COST-10b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- COST-13a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- COST-13b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- COST-14a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- COST-14b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- SUITE-1: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-1b: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SUITE-2a: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-2c: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SUITE-2d: `when: suite-owner = dev` (was size = S); roles unchanged
- SUITE-2b: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-2e: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SUITE-3: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-4: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-4b: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SUITE-5: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-5b: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SUITE-3b: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SUITE-6: `when: suite-owner = tech-lead` (was size = L); roles unchanged
- SUITE-6b: `when: suite-owner = qa-white` (was size = M); roles unchanged
- SPAWN-5a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- SPAWN-5b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- SPAWN-8a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- SPAWN-8b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- SPAWN-9: `when: plan-owner = team-lead` (was size = L); roles unchanged
- SPAWN-10a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- SPAWN-10b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- SAFE-9: `when: (none)` (was size in M, L); roles unchanged
- SAFE-10: `when: (none)` (was size in M, L); roles unchanged
- MSG-6: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-11a: `when: plan-owner = manager` (was size in S, M); roles unchanged
- MSG-11b: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-12: `when: doubt-owner = ba` (was size = L); roles unchanged
- MSG-13: `when: plan-owner = team-lead` (was size = L); roles unchanged
- MSG-16a: `when: doubt-owner = manager and design = yes` (was size in S, M and design = yes); roles unchanged
- MSG-16b: `when: doubt-owner = ba and design = yes` (was size = L and design = yes); roles unchanged
- MSG-20a: `when: doubt-owner = manager and architecture = yes` (was size in S, M and architecture = yes); roles unchanged
- MSG-20b: `when: doubt-owner = ba and architecture = yes` (was size = L and architecture = yes); roles unchanged
- SPAWN-2a: `when: plan-owner = manager` (was size = S); roles unchanged
- SPAWN-2b: `when: plan-owner = team-lead` (was size = M and qa-b = yes); roles unchanged
- SPAWN-2c: `when: plan-owner = team-lead` (was size = L and qa-b = yes); roles unchanged

## v8 — 2026-10-27
- snapshot: history/process-v8/

The optional Architect (`architecture: yes`); every rule below composes only with the flag on, so a scope with it `no` is unchanged.

added:
- SIZE-3a: the `architecture:` flag, PO only (only with `architecture: yes`)
- SIZE-9a: the Architect delivers `architecture.md`
- SIZE-22a: duty owners with an Architect (rows replace SIZE-22's)
- SIZE-23c: `architecture.md` conformance in the technical AC, M
- SIZE-23d: `architecture.md` conformance in the technical AC, L
- REV-22a: the S review subagent checks conformance to `architecture.md`
- WHO-2e: Architect owns the architecture; the PO decides irreversible choices
- SPAWN-4a: when and how the Manager spawns and retires the Architect
- START-4a: Architect role-short `arch`
- START-5a: Architect lifetime row
- START-20: Architect start
- LC-11c: S and M plan waits for `architecture.md` final
- LC-11d: L plan waits for `architecture.md` final
- LC-19c: Developer builds inside `architecture.md`
- MSG-20: follow `architecture.md` or `ASK` the Architect; 2 rounds then the Manager
- MSG-20a: Architect doubts and final, S and M
- MSG-20b: Architect doubts and final, L

changed:
- none

removed:
- none

retargeted:
- FILE-11: the Architect drafts ADR text in `tasks/` too
- COST-1: the Architect carries it too (only with `architecture: yes`)
- COST-2: the Architect carries it too (only with `architecture: yes`)
- COST-3: the Architect carries it too (only with `architecture: yes`)
- COST-7: the Architect carries it too (only with `architecture: yes`)
- COST-9: the Architect carries it too (only with `architecture: yes`)
- MSG-1: the Architect carries it too (only with `architecture: yes`)
- MSG-10: the Architect carries it too (only with `architecture: yes`)
- MSG-2: the Architect carries it too (only with `architecture: yes`)
- MSG-9: the Architect carries it too (only with `architecture: yes`)
- SAFE-2: the Architect carries it too (only with `architecture: yes`)
- SAFE-5: the Architect carries it too (only with `architecture: yes`)
- START-7: the Architect carries it too (only with `architecture: yes`)
- START-9: the Architect carries it too (only with `architecture: yes`)

## v7 — 2026-10-22
- snapshot: history/process-v7/

Format from v7: `added:`, `changed:`, `removed:`, `retargeted:` list rule IDs with the why per item; `none` when empty.
`squad-process upgrade` reads the rule files themselves; these lines are the PO-facing reason.

added:
- CORE-1: converted from P:206
- CORE-2: converted from P:164, P:168, P:169 ...
- CORE-3: converted from P:192
- CORE-4: converted from P:181
- CORE-5: converted from P:40
- FILE-1: converted from P:16, P:17, P:18 ...
- FILE-2: converted from P:31, P:32, P:33 ...
- FILE-3: converted from P:41, P:43
- FILE-4: converted from P:42, agents/manager.md:28, agents/team-lead.md:28
- FILE-5a: converted from agents/manager.md:28
- FILE-5b: converted from agents/manager.md:28
- FILE-5c: converted from agents/team-lead.md:28
- FILE-6: converted from P:47, P:48, P:49 ...
- FILE-7: converted from P:53, P:54
- FILE-8: converted from P:52
- FILE-9: converted from P:55, P:56, P:57
- FILE-10: converted from P:61, P:62, P:63
- START-1: converted from P:67, P:70, P:71
- START-2a: converted from P:69, agents/manager.md:27
- START-2b: converted from P:69, P:79, agents/team-lead.md:24
- START-2c: converted from agents/manager.md:27, agents/manager.md:52
- START-2d: converted from fix b
- START-3: converted from P:75, P:78, P:79
- START-4: converted from P:76, P:77
- START-5: converted from P:85, P:86, P:87 ...
- START-6: converted from agents/team-lead.md:12, agents/tech-lead.md:10, agents/ba.md:10 ...
- START-7: converted from agents/team-lead.md:12, agents/tech-lead.md:10, agents/ba.md:10 ...
- START-8: converted from agents/qa-blackbox.md:10
- START-9: converted from agents/team-lead.md:13, agents/tech-lead.md:12, agents/ba.md:11 ...
- START-10: converted from agents/dev.md:11, agents/dev.md:12, agents/dev.md:13
- START-11: converted from agents/ba.md:12
- START-12: converted from agents/designer.md:12
- START-13: converted from agents/qa-blackbox.md:11
- START-14: converted from agents/qa-whitebox.md:11
- START-15: converted from agents/team-lead.md:14
- START-16: converted from agents/tech-lead.md:11
- START-17: converted from agents/token-coach.md:10, agents/token-coach.md:11
- START-18: converted from agents/manager.md:10, agents/manager.md:11, agents/manager.md:12 ...
- START-19: converted from agents/manager.md:20, agents/manager.md:21
- SIZE-1: converted from P:95
- SIZE-2: converted from P:99, P:100, P:101
- SIZE-3: converted from P:103
- SIZE-4: converted from P:105, P:106, P:107
- SIZE-5a: converted from P:113
- SIZE-5b: converted from P:113
- SIZE-6a: converted from P:114, agents/tech-lead.md:18
- SIZE-6b: converted from P:114, P:121
- SIZE-7a: converted from P:115
- SIZE-7b: converted from P:115
- SIZE-8a: converted from P:116, agents/dev.md:24
- SIZE-8b: converted from P:116
- SIZE-9: converted from P:117
- SIZE-10a: converted from P:118, agents/dev.md:20
- SIZE-10b: converted from P:118
- SIZE-11a: converted from P:119, agents/tech-lead.md:19
- SIZE-11b: converted from P:119, agents/ba.md:23
- SIZE-12: converted from P:109 (heading)
- SIZE-13: converted from P:125, agents/manager.md:25
- SIZE-14: converted from P:125, agents/tech-lead.md:19
- SIZE-15: converted from P:126, agents/manager.md:25
- SIZE-16: converted from P:127, P:128, agents/manager.md:25 ...
- SIZE-17a: converted from agents/ba.md:21
- SIZE-17b: converted from agents/team-lead.md:6
- SIZE-17c: converted from agents/qa-whitebox.md:25
- SIZE-17d: converted from agents/qa-blackbox.md:22
- SIZE-18: converted from agents/manager.md:26
- GOAL-1: converted from P:132, P:133, agents/manager.md:62 ...
- GOAL-2: converted from P:134, P:135, P:136
- GOAL-3a: converted from P:136, agents/tech-lead.md:21
- GOAL-3b: converted from P:136, agents/qa-whitebox.md:23
- GOAL-4: converted from P:142
- GOAL-5: converted from P:137, P:138, agents/manager.md:55
- GOAL-6a: converted from P:139, P:140, agents/tech-lead.md:24
- GOAL-6b: converted from agents/dev.md:30
- GOAL-6c: converted from P:139
- GOAL-7: converted from P:141, agents/manager.md:32
- PROMO-1: converted from P:146
- PROMO-2: converted from P:148, agents/tech-lead.md:22
- PROMO-3a: converted from P:148, agents/ba.md:22
- PROMO-3b: converted from P:148
- PROMO-4: converted from P:149
- PROMO-5: converted from agents/dev.md:30
- PROMO-6: converted from P:150, P:151, agents/manager.md:67
- PROMO-7: converted from P:152
- PROMO-8: converted from agents/qa-whitebox.md:24
- CLOSE-1: converted from P:156, agents/manager.md:72
- CLOSE-2: converted from P:157, agents/manager.md:72
- CLOSE-3a: converted from P:158, agents/tech-lead.md:23
- CLOSE-3b: converted from P:158, agents/manager.md:66
- CLOSE-4: converted from P:159, agents/manager.md:68
- CLOSE-5: converted from P:160
- MSG-1: converted from P:164, P:168, P:169 ...
- MSG-2: converted from P:176
- MSG-3: converted from P:177, log row 46
- MSG-4a: converted from P:178
- MSG-4b: converted from P:178
- MSG-5: converted from P:179
- MSG-6: converted from P:180, agents/team-lead.md:35, agents/team-lead.md:39 ...
- MSG-7a: converted from P:182, agents/manager.md:32
- MSG-7b: converted from P:182, agents/manager.md:32
- MSG-8a: converted from P:183
- MSG-8b: converted from P:183, agents/team-lead.md:26
- MSG-9: converted from P:184
- MSG-10: converted from P:185
- MSG-11a: converted from agents/dev.md:21
- MSG-11b: converted from agents/dev.md:21
- MSG-12: converted from agents/ba.md:20
- MSG-13: converted from agents/team-lead.md:20
- MSG-14: converted from agents/tech-lead.md:30
- MSG-15: converted from agents/tech-lead.md:33
- MSG-16a: converted from agents/designer.md:20
- MSG-16b: converted from agents/designer.md:20
- MSG-17: converted from agents/designer.md:19
- MSG-18: converted from agents/manager.md:29
- MSG-19: converted from agents/team-lead.md:27
- WHO-1a: converted from P:193, P:197
- WHO-1b: converted from P:191, P:193, P:197
- WHO-2: converted from P:192, P:198
- WHO-2b: converted from P:196
- WHO-2c: converted from P:196
- WHO-3a: converted from P:194
- WHO-3b: converted from P:194
- WHO-4: converted from P:195
- WHO-5: converted from P:199, P:200, agents/manager.md:31
- WHO-6: converted from P:5, agents/manager.md:30
- WHO-7: converted from P:202
- WHO-8: converted from agents/manager.md:32
- WHO-8a: converted from agents/manager.md:32
- WHO-8b: converted from agents/manager.md:32
- WHO-8c: converted from agents/team-lead.md:29
- LC-1: converted from P:208
- LC-2: converted from P:209
- LC-3a: converted from P:210, agents/dev.md:31
- LC-3b: converted from P:210, log row 35
- LC-4: converted from P:211
- LC-5: converted from P:212
- LC-6: converted from P:213
- LC-7a: converted from P:218, agents/manager.md:90
- LC-7b: converted from P:218, agents/manager.md:90, agents/team-lead.md:26
- LC-8: converted from log row 39
- LC-9: converted from log row 42
- LC-10: converted from agents/tech-lead.md:17
- LC-11: converted from agents/tech-lead.md:29
- LC-12: converted from agents/tech-lead.md:31
- LC-13: converted from agents/tech-lead.md:32
- LC-14: converted from agents/tech-lead.md:18, agents/tech-lead.md:26
- LC-15: converted from agents/team-lead.md:21, agents/team-lead.md:22
- LC-16: converted from agents/team-lead.md:21, agents/team-lead.md:22
- LC-17: converted from agents/team-lead.md:25, agents/team-lead.md:54
- LC-18: converted from agents/dev.md:18, agents/dev.md:19, agents/dev.md:22
- LC-19: converted from agents/dev.md:20
- LC-20a: converted from agents/dev.md:35
- LC-20b: converted from agents/dev.md:35
- LC-21: converted from P:216
- LC-22a: converted from P:217
- LC-22b: converted from P:217
- LC-23: converted from agents/designer.md:17, agents/designer.md:18
- REV-1: converted from agents/tech-lead.md:19, agents/tech-lead.md:29
- REV-2: converted from agents/qa-whitebox.md:17, agents/qa-whitebox.md:18, agents/qa-whitebox.md:19 ...
- REV-3: converted from log row 38
- REV-4: converted from P:214, agents/tech-lead.md:27, agents/qa-whitebox.md:22
- REV-5a: converted from P:214, agents/tech-lead.md:27
- REV-5b: converted from P:214, agents/tech-lead.md:27, agents/qa-whitebox.md:22
- REV-6: converted from P:215, agents/tech-lead.md:27, agents/qa-whitebox.md:22
- REV-7: converted from agents/tech-lead.md:28, agents/qa-whitebox.md:16
- REV-8: converted from agents/ba.md:19, agents/qa-blackbox.md:20
- REV-9: converted from agents/qa-blackbox.md:21
- REV-10: converted from agents/qa-whitebox.md:26
- REV-11: converted from agents/qa-blackbox.md:23
- REV-12: converted from agents/qa-whitebox.md:27, agents/qa-blackbox.md:24
- REV-13a: converted from agents/dev.md:24, agents/dev.md:26
- REV-13b: converted from agents/dev.md:26
- REV-14a: converted from agents/dev.md:28
- REV-14b: converted from agents/dev.md:28
- REV-15: converted from agents/dev.md:27
- REV-16: converted from log row 48
- REV-17: converted from log row 48
- REV-18a: converted from log row 49
- REV-18b: converted from log row 49
- EVID-1: converted from P:219
- EVID-2a: converted from P:220
- EVID-2b: converted from P:220, agents/dev.md:29
- EVID-2c: converted from P:220, agents/tech-lead.md:19
- EVID-3a: converted from P:221
- EVID-3b: converted from P:221
- EVID-4: converted from agents/dev.md:24
- EVID-5: converted from agents/dev.md:20
- ITER-1: converted from P:225, P:227, P:228 ...
- ITER-2: converted from agents/manager.md:94
- ITER-3: converted from agents/team-lead.md:45
- ITER-4: converted from agents/manager.md:95
- ITER-5: converted from agents/manager.md:96, agents/manager.md:97
- ITER-6: converted from P:234
- ITER-6a: converted from P:234
- ITER-6b: converted from P:234
- ITER-7: converted from P:235, agents/token-coach.md:16, agents/token-coach.md:18
- ITER-8: converted from agents/token-coach.md:15, agents/token-coach.md:16, agents/token-coach.md:17
- ITER-9: converted from P:237, agents/token-coach.md:22, agents/token-coach.md:23 ...
- ITER-10: converted from P:236
- ITER-11: converted from agents/manager.md:98, agents/manager.md:99
- ITER-12: converted from agents/manager.md:100
- COST-1: converted from P:241, agents/team-lead.md:15, agents/tech-lead.md:13 ...
- COST-2: converted from P:243
- COST-3: converted from P:244
- COST-4a: converted from log row 37
- COST-4b: converted from log row 34
- COST-5: converted from P:244, log row 40
- COST-6a: converted from log row 40, log row 47
- COST-6b: converted from log row 40, log row 47
- COST-7: converted from log row 44
- COST-8: converted from P:245, log row 33, log row 41
- COST-9: converted from P:246
- COST-10a: converted from log row 45
- COST-10b: converted from log row 45
- COST-11: converted from P:247
- COST-12: converted from P:248
- NOTE-1: converted from P:59, P:252, P:254 ...
- NOTE-2: converted from P:257, P:258, agents/manager.md:111
- NOTE-3: converted from agents/team-lead.md:54
- SAFE-1a: converted from P:262, agents/dev.md:25
- SAFE-1b: converted from agents/manager.md:104
- SAFE-2: converted from P:268, agents/manager.md:31
- SAFE-3: converted from P:275
- SAFE-4: converted from P:276
- SAFE-5: converted from log row 43
- SAFE-6: converted from agents/manager.md:105
- SAFE-7: converted from agents/manager.md:14, agents/manager.md:106
- SAFE-8: converted from agents/designer.md:25
- SAFE-9: converted from agents/qa-whitebox.md:35
- SAFE-10: converted from agents/qa-blackbox.md:16
- SUITE-1: converted from P:269
- SUITE-2a: converted from P:270, agents/dev.md:23
- SUITE-2b: converted from P:270
- SUITE-3: converted from P:271, agents/tech-lead.md:25
- SUITE-4: converted from P:272, agents/tech-lead.md:25
- SUITE-5: converted from P:273, agents/tech-lead.md:25
- SUITE-6: converted from P:274
- MRG-1: converted from P:263, P:264
- MRG-2: converted from P:265
- MRG-3: converted from P:266
- MRG-4: converted from P:267
- SPAWN-1: converted from agents/manager.md:44, agents/manager.md:46, agents/manager.md:47 ...
- SPAWN-2a: converted from agents/manager.md:50
- SPAWN-2b: converted from agents/manager.md:50
- SPAWN-3: converted from agents/manager.md:51
- SPAWN-4: converted from agents/manager.md:54
- SPAWN-5a: converted from agents/manager.md:55
- SPAWN-5b: converted from agents/team-lead.md:23
- SPAWN-6: converted from agents/manager.md:56
- SPAWN-7: converted from agents/manager.md:57
- SPAWN-8a: converted from agents/manager.md:58
- SPAWN-8b: converted from agents/manager.md:58, agents/team-lead.md:23
- SPAWN-9: converted from agents/team-lead.md:33
- SPAWN-10a: converted from agents/manager.md:84, agents/manager.md:86, agents/manager.md:87 ...
- SPAWN-10b: converted from agents/manager.md:78, agents/manager.md:80, agents/manager.md:81 ...
- SPAWN-11: converted from agents/manager.md:76
- CLOSE-3c: new for the size model: closing by size
- COST-5a: new for the size model: cost rules retargeted: Manager retires and respawns at S and M
- EVID-2d: new for the size model: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-2e: new for the size model: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- GOAL-3c: new for the size model: goal duties by size
- GOAL-6d: new for the size model: goal duties by size
- ITER-3b: new for the size model: iteration duties by size
- LC-11b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-17b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-19b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-20c: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-22c: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-25: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-26: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-2b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-5b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-6b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-7c: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-8b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-8c: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-9b: new for the size model: lifecycle duties retargeted by size; 3 returns and advisor rules
- MSG-17b: new for the size model: message routes by size: S and M to the Manager, L to the Team Lead
- PROMO-5b: new for the size model: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- REV-14c: new for the size model: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-19b: new for the size model: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-21b: new for the size model: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-22: new for the size model: the S review subagent runs on Sonnet at high effort (`model: sonnet`, `effort: high`, a new agent not a fork; PO 2026-10-22); Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-2b: new for the size model: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-3b: new for the size model: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- SIZE-17e: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-21a: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-21b: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-22: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-23b: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-24b: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-5c: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-6c: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-6d: new for the size model: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SPAWN-2c: new for the size model: spawning by size: Manager at S and M, Team Lead at L
- SUITE-1b: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-2c: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-2d: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-2e: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-3b: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-4b: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-5b: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-6b: new for the size model: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- WHO-2d: new for the size model: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- START-3b: new (ticket 20): the Manager shows the team's models with the size, the PO's answer goes to scope.md
- ITER-6c: new: the Manager waits for the Token Coach's message and never polls for its file

changed:
- none

removed:
- SIZE-21: replaced by SIZE-21a and SIZE-21b (QA blackbox off, split by size)

retargeted:
- SAFE-11: scratch dirs: `cd` out before `rm`; Claude Code denies removing the cwd or an ancestor
- SIZE-1: points at START-3b: the size proposal carries the team's models
- ITER-6: the spawn line carries --prompt (scope, output file, message back); the Coach no longer starts idle
- SIZE-23c: QA whitebox checks the diff against `architecture.md` whenever it is on the team (`qa-white = yes and architecture = yes`); adds it to the AC when it owns it
- SIZE-23d: acts for the Tech Lead only (`tech-ac = tech-lead and architecture = yes`); QA whitebox's check moved to SIZE-23c so no absent role acts
- SIZE-17a: also gated on `ba = yes`, so it composes only for a BA on the team
- SIZE-17b: also gated on `team-lead = yes`
- SIZE-17c: also gated on `qa-white = yes`
- SIZE-17d: also gated on `qa-black = yes`
- SIZE-17e: also gated on `tech-lead = yes`
- SIZE-18: extra hands only exist at L: when size = L
- SPAWN-4: the Manager's plan, not the absent Tech Lead's (S and M)
- CLOSE-1: closing keeps the Manager on scope and goal close (squad-close spares it); squad close still retires all
- CLOSE-2: closing keeps the Manager on scope and goal close (squad-close spares it); squad close still retires all
- CLOSE-3a: closing by size
- CLOSE-4: closing keeps the Manager on scope and goal close (squad-close spares it); squad close still retires all
- CLOSE-5: closing keeps the Manager on scope and goal close (squad-close spares it); squad close still retires all
- CORE-3: core rule wording by size
- COST-10a: cost rules retargeted: Manager retires and respawns at S and M
- COST-10b: cost rules retargeted: Manager retires and respawns at S and M
- COST-11: cost rules retargeted: Manager retires and respawns at S and M
- COST-13a: cost rules retargeted: Manager retires and respawns at S and M
- COST-13b: cost rules retargeted: Manager retires and respawns at S and M
- COST-14a: cost rules retargeted: Manager retires and respawns at S and M
- COST-14b: cost rules retargeted: Manager retires and respawns at S and M
- COST-4a: cost rules retargeted: Manager retires and respawns at S and M
- COST-4b: cost rules retargeted: Manager retires and respawns at S and M
- COST-5: cost rules retargeted: Manager retires and respawns at S and M
- COST-6a: cost rules retargeted: Manager retires and respawns at S and M
- COST-6b: cost rules retargeted: Manager retires and respawns at S and M
- EVID-1: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-2b: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-2c: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-3a: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-3b: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-4: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-5: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- EVID-7: evidence assembled and confirmed by the size's owner (Manager S, M; Tech Lead L)
- FILE-10: file owners by size
- FILE-5a: file owners by size
- FILE-5b: file owners by size
- FILE-5c: file owners by size
- FILE-6: file owners by size
- FILE-7: file owners by size
- FILE-8: file owners by size
- FILE-9: file owners by size
- GOAL-2: goal duties by size
- GOAL-3a: goal duties by size
- GOAL-3b: goal duties by size
- GOAL-4: goal duties by size
- GOAL-5: goal duties by size
- GOAL-6a: goal duties by size
- GOAL-6b: goal duties by size
- GOAL-6c: goal duties by size
- ITER-11: iteration duties by size
- ITER-3: iteration duties by size
- LC-1: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-10: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-11: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-12: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-13: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-14: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-15: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-16: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-17: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-18: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-19: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-2: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-20a: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-20b: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-21: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-22a: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-22b: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-4: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-5: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-6: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-7a: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-7b: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-8: lifecycle duties retargeted by size; 3 returns and advisor rules
- LC-9: lifecycle duties retargeted by size; 3 returns and advisor rules
- MSG-11a: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-11b: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-12: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-13: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-14: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-15: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-16a: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-16b: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-17: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-18: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-19: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-3: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-4a: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-4b: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-5: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-6: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-7a: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-7b: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-8a: message routes by size: S and M to the Manager, L to the Team Lead
- MSG-8b: message routes by size: S and M to the Manager, L to the Team Lead
- NOTE-1: notes by size
- NOTE-3: notes by size
- PROMO-1: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- PROMO-2: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- PROMO-3a: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- PROMO-3b: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- PROMO-4: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- PROMO-5: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- PROMO-6: promote.md owner by size: Developer S, QA whitebox M, Tech Lead L
- REV-1: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-13a: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-14a: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-14b: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-15: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-16: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-19: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-2: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-21: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-3: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-4: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-5a: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-6: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-7: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- REV-8: code and behaviour check by size: Developer + Sonnet review (high effort) at S, QA whitebox/blackbox at M and L
- SAFE-10: safety wording by size
- SAFE-9: safety wording by size
- SIZE-10a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-11a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-11b: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-12: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-13: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-14: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-15: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-16: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-17a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-17b: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-2: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-4: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-5a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-5b: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-6a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-6b: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-7a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SIZE-8a: sizes S/M/L: S = Manager + Developers, M adds both QAs, L every role; duties move to the present role
- SPAWN-10a: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-10b: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-2a: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-2b: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-5a: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-5b: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-8a: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-8b: spawning by size: Manager at S and M, Team Lead at L
- SPAWN-9: spawning by size: Manager at S and M, Team Lead at L
- START-10: start and spawn rules by size: Manager spawns and caps Developers at S and M
- START-2a: start and spawn rules by size: Manager spawns and caps Developers at S and M
- START-2b: start and spawn rules by size: Manager spawns and caps Developers at S and M
- START-2c: start and spawn rules by size: Manager spawns and caps Developers at S and M
- START-2d: start and spawn rules by size: Manager spawns and caps Developers at S and M
- START-6: start and spawn rules by size: Manager spawns and caps Developers at S and M
- START-5: lifetime row: the Manager stays, chat-only, after a scope close until the PO retires it
- SUITE-1: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-2a: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-2b: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-3: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-4: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-5: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- SUITE-6: full suite owner by size: Developer S, QA whitebox M, Tech Lead L
- WHO-1a: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-1b: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-2: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-2b: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-2c: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-3a: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-3b: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-8a: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-8b: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)
- WHO-8c: owner table per size: Manager (S, M) or Team Lead/Tech Lead (L)

## v6 — 2026-10-19
- snapshot: history/process-v6.md

### Files table: evidence next to the ticket
- sections: ## Files are the truth, messages are the talk
- change: rule
- why: PO wants evidence next to each ticket with screenshots shown in the markdown
- old: snapshot
- new: snapshot

### Evidence rules in the task lifecycle
- sections: ## Task lifecycle
- change: rule
- why: PO wants evidence next to each ticket with screenshots shown in the markdown
- old: snapshot
- new: snapshot

### Merge accepts the evidence sha; receipts stay in the scope folder
- sections: ## Safety
- change: rule
- why: PO wants evidence next to each ticket with screenshots shown in the markdown
- old: snapshot
- new: snapshot

### Sizes rows name `evidence.md`
- sections: ### When a role is left out, its duties move. They are never dropped.
- change: rule
- why: PO wants evidence next to each ticket with screenshots shown in the markdown
- old: snapshot
- new: snapshot

## v5 — 2026-10-19
- snapshot: history/process-v5.md

### Task ID is the ticket number
- sections: ## Messages
- change: rule
- why: every agent writes the bare ticket number as the task ID, so messages and roster rows name one thing
- old: snapshot
- new: snapshot

## v4 — 2026-10-17
- snapshot: history/process-v4.md

### Files table: Team Lead rows
- sections: ## Files are the truth, messages are the talk
- change: rule
- why: the Team Lead keeps its Developers' roster rows, owns the plan file in M and L, and writes the iteration summary the Manager reads
- old: snapshot
- new: snapshot

### Developer cap shared out by the Team Lead
- sections: ## Defaults
- change: rule
- why: the Team Lead spawns Developers up to the cap; a goal Manager divides the cap among running scopes
- old: snapshot
- new: snapshot

### Team Lead spawns the Developers in M and L
- sections: ## Starting work
- change: rule
- why: in M and L the Team Lead spawns and retires the Developers; the Manager's confirm gate for its own spawns stays
- old: snapshot
- new: snapshot

### M gains the Team Lead
- sections: ## Sizes: not every scope runs the full pod; ### When a role is left out, its duties move. They are never dropped.
- change: rule
- why: M runs the plan, order and assignment through the Team Lead, who keeps the Manager out of the pod's traffic; S is unchanged
- old: snapshot
- new: snapshot

### Size changes and handover with a Team Lead
- sections: ### Changing size
- change: rule
- why: the Manager retires the roles that drop out when a scope moves down; a joining Team Lead takes the plan over from the Handover
- old: snapshot
- new: snapshot

### Base branch checked by the Manager
- sections: ## Inside a goal
- change: rule
- why: the Team Lead spawns with the base the Manager checked and named
- old: snapshot
- new: snapshot

### Pod contact and Team Lead rulings
- sections: ## Messages
- change: rule
- why: pod members message the Team Lead, which reports to the Manager only four things; the Team Lead's ruling follows the FINAL: rule; nobody relays a blocked pane
- old: snapshot
- new: snapshot

### Owners and escalation of plan and Developer duties
- sections: ## Who decides
- change: rule
- why: the Team Lead decides plan, order and assignment disputes in M and L and owns Developer spawning there
- old: snapshot
- new: snapshot

### 3 returns handled by the Team Lead
- sections: ## Task lifecycle
- change: rule
- why: the Team Lead steps in after 3 returns on one task in M and L
- old: snapshot
- new: snapshot

### Only the Tech Lead runs the full suite
- sections: ## Safety; ## Inside a goal; ## Task lifecycle
- change: rule
- why: PO note 2026-10-17: Developers and QAs run only the test files they touched, never the full suite or two runs at once; the Tech Lead decides when it runs and saves the receipt
- old: snapshot
- new: snapshot

## v3 — 2026-10-16
- snapshot: history/process-v3.md

### Board removed
- sections: ## Messages
- change: reword
- why: the squad board is removed, so the Manager no longer reads it
- old:
```
- The Manager never pushes `STATUS`: it reads the board, logs, roster and task file first, and pings an agent only after 10 minutes of no pane activity.
```
- new:
```
- The Manager never pushes `STATUS`: it reads logs, the roster and the task file first, and pings an agent only after 10 minutes of no pane activity.
```

## v2 — 2026-10-15
- snapshot: history/process-v2.md

### Tighten the wording of every section
- sections: all
- change: reword
- why: roles read process.md at every start, so wording is tightened in all sections and no rule changed; the rule for editing the file now lives in the Manager's instructions
- old: snapshot
- new: snapshot

### Long suites: lock for browser files, time pass only when needed
- sections: ## Safety
- change: rule
- why: only the browser files need the lock and the runner skips phases the diff cannot affect, so suite runs no longer queue behind each other; the `flock ... nice -n 10` command text goes because the runner owns the lock, and the Developer now runs the suite in the background and waits for its completion notice (never `pgrep -f` or `pkill -f`)
- old:
```
- **Long suites: run once, read the receipt.** For a suite longer than ~2 minutes, one full run at a time for the whole squad, under a lock: `flock /tmp/<squad>-suite.lock nice -n 10 <suite command>` (a project may ship a runner that takes the lock and writes the receipts; `project.md` names it). The Developer runs the full suite once, on the final sha after every fix is in (while building, only the files it touched), and saves a receipt whose first line is `sha <git rev-parse HEAD> clean=<yes|no>` and whose tail is the suite's OK line. QA checks the receipt (same sha as the `HANDIN`, clean tree, OK), then runs only the targeted tests for the files in the diff and reads the diff; it runs the full suite itself only when the receipt is missing or its sha differs (an integration task is no exception). Targeted runs are free; the full suite is never started in the background while you wait on something else.
```
- new:
```
- **Long suites: run once, read the receipt.** A suite over ~2 minutes runs once per task. `project.md` may name the runner; it locks only its browser files and skips phases the diff cannot affect.
  - The Developer runs the full suite once, on the final sha after every fix, in the background, waits for its completion notice (never `pgrep -f` or `pkill -f`) and saves a receipt: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the suite's OK line. While building, only touched files.
  - QA checks the receipt (same sha as the `HANDIN`, clean tree, OK, its skipped-phase lines), then runs only targeted tests for the diff's files and reads the diff. It runs the full suite only when the receipt is missing or its sha differs, integration tasks included. Targeted runs are free.
```
