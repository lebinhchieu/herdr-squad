// Bodies for the markdown-subset parser (IV-01). Not part of FIXTURES: those are `list --json` output.
// Real samples, verbatim: e1, e2 (`.claude/squads/plugin/scopes/inbox-visual/inbox.jsonl`, seen rows E1 and E2, 2026-10-16;
// the `<br>` line breaks are as the CLI stored them), E1_REC and E1_OPTIONS (the same row's rec and options cells), escalationsTable (whole file
// `.claude/squads/squad-board/scopes/_done/board/escalations.md`, the only done-scope escalation file with a table).
// Written by hand from the QA blackbox hostile list (`evidence/qa-b-spec-review.md` -> Fixtures): the rest.
// The 10,000-character line and the 5,000 `**` are built in markup.test.ts, not stored.

export const E1_TITLE = "inbox-visual: what should 'visual' mean in the terminal inbox?"

export const E1_REC = "(c), built (a) first: visual-answer step 12 says the terminal never carries a diagram, so real visuals need a page; (b) is cheap polish on top"
export const E1_OPTIONS = "(a) Attached page: each item can carry a visual page (HTML or blueprint-markdown, made with /visual-answer); the inbox shows a one-key 'open visual' and keeps a short text summary; (b) Richer terminal render: options as side-by-side cards, recommendation highlighted, tables and ASCII structure inside the pane, no external page; (c) Both: (a) for diagrams, (b) for options/recommendation layout"

export const VISUAL: Record<string, string> = {
  e1: "inbox-visual: what should 'visual' mean in the terminal inbox?<br>Brief: \"the inbox only shows prose, make it show a visual result, refer to /visual-answer\".<br><br>The inbox is a Claude Code mod (hooks/po-inbox/ui.tsx) that can draw only Text/Box/Button. The visual-answer skill itself says a terminal never carries a diagram: visuals go into a file or a page.<br><br>Also confirm:<br>1. Size M (BA, Tech Lead, both QAs, Devs ≤3). Signals: user-visible change, ~3-5 tasks, touches hooks/po-inbox, bin/squad-inbox, agents/manager.md, tests. No risk flag. If you'd rather the BA explore the meaning instead of you answering here, I'd size it L.<br>2. Changing agents/manager.md (telling Managers to attach a visual) is a role-instruction change: OK to include as a ticket, approved at check-in?<br>3. Should every item get a visual, or only `answer` items (decisions), with `read` items staying text?",
  e2: "inbox-visual: clarify what the TUI inbox should show<br>Since Managers get no new instruction, the inbox must make what they already write look structured. Today the item pane prints the body line by line, options as plain \"(a) text\" lines, and the recommendation dimmed (hooks/po-inbox/ui.tsx body/answerForm).<br><br>1. Which screens change?<br>   [rec] the item screen (body, options, recommendation) first; the list and the band only get colour for kind/blocks. Not the Done screen.<br><br>2. Body text: render the markdown Managers already write (headings, bullets, numbered lists, **bold**, `code`, tables, \"[rec]\"-style tags) as TUI structure and colour?<br>   [rec] yes, a small markdown subset; anything else stays plain text, never dropped.<br><br>3. Options: show each option as a block, with the recommended one marked (colour + \"recommended\" tag), instead of the dimmed line under the list?<br>   [rec] yes; match the recommendation to an option by its key (\"(c)\") when the Manager names one; otherwise keep the recommendation as its own line.<br><br>4. Colour meanings: fixed roles taken from your visual-answer table, mapped to Claude Code theme colours: green = pass/recommended, red = fail/blocking, amber = warning/not verified, dim = metadata.<br>   [rec] yes, one meaning per colour across band, list and item.<br><br>5. Narrow panes (under ~60 columns, the existing compact cut-off): stack everything in one column, no side-by-side.<br>   [rec] yes; wide panes may show options side by side only if the Designer proposes it.<br><br>6. Any new `squad-inbox add` field (e.g. a typed \"table\" or \"status\" field)?<br>   [rec] no: the PO said no new instruction for Managers, so no new field for them to fill.<br><br>7. Designer's output: a design file per screen with ASCII mock-ups of each state, you approve it before any Developer starts.<br>   [rec] yes.",
  escalationsTable: "# Escalations\n\n**Questions waiting on the PO, newest first. The Manager writes each one before telling the PO.**\n\n| # | Date | Question | Options | Manager's recommendation | Blocks | Answer |\n|---|---|---|---|---|---|---|\n| 1 | 2026-10-12 | goal.md sets size S but also says done = QA whitebox PASS. S has no QA whitebox, allows 1–2 tasks, and no risk flag; this scope has about 10 tasks and a security flag (localhost bind, token-guarded jump). Which size? | A) S + QA whitebox: Tech Lead plans, QA whitebox signs off, Developer evidence replaces QA blackbox. Logged as a process exception. B) Full M: add a BA and a QA blackbox (testing via replay mode). C) S exactly as in process.md: Tech Lead review only. | **A.** The spec is complete, so a BA adds little. QA whitebox matches goal.md's done rule and covers the security flag. Revisit QA blackbox in iteration 2 when the page exists. | Spawning anyone | 2026-10-12: A |\n| 2 | 2026-10-12 | BRD-02..06 must branch from code that has BRD-01, and only the PO merges. When BRD-01 passes QA whitebox, will you merge `squad/dev-board-1` into `squad-board-spec`? Please also commit the tickets, `design.md` and the `--effort` change first, so new worktrees have them. | A) PO merges BRD-01 as soon as it passes, and the Manager pings you. B) Developers stack on `squad/dev-board-1`, branching from it by hand; this needs a base-ref option in squad-spawn, which is outside the goal. | **A.** One merge unblocks 5 tickets. | BRD-02..06 | 2026-10-12: PO delegated decisions to the Manager. Manager chose **stacking**: the Manager creates each worktree from the passed BRD-01 commit before `squad-spawn`, which reuses it. A final integration ticket combines the passed branches on one Developer branch. The PO merges once at the end. |\n| 3 | 2026-10-12 | The Developer permission settings deny `git merge`, so dev-board-8 can't merge the passed branches into its own BRD-09 branch. The Manager's stacked-branches plan missed this; neither the Manager nor an agent may work around it. | A) Allow merge for this run: remove `Bash(git merge:*)` from the project copy `squad/settings/dev.json` only (the plugin template stays). `git push`, `rebase`, `reset --hard` and `checkout main` stay denied. B) The PO runs the merges into `squad/dev-board-8` by hand (5 now, 1 more for BRD-06, ~7 in iteration 2). C) The PO merges each passed branch into `squad-board-spec` as it passes, as in the original process. | **A.** It's one change, and it ends the blocks for both integrations. The process already limits merges to a Developer's own branch. | BRD-09, then BRD-08 and all of iteration 2 | 2026-10-12: A (PO). Done: merge allowed in squad/settings/dev.json. |\n| 4 | 2026-10-12 | Usage limits: account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h, burning about 1% of 7d every 5 min with 5 agents working. Account 1 was at 91% 7d 7 h ago (resets Tue 09:00), and its token has expired, so the auto-switch can't see it or switch to it. Iteration 2 (8 tickets) won't fit in what's left. | A) Finish what's in flight (BRD-08, 18, 10, 12 and their reviews), spawn nothing new, then pause cleanly with notes saved; resume after Tue 09:00. B) Keep full speed until the limit stops the squad wherever it is (files are the truth, so it can resume, but mid-task sessions are lost). C) Move Developers to a cheaper model. | **A**, plus the PO runs `c1` once (then `/exit`) to refresh account 1's token so the switcher can use its last ~9%. C trades away the quality bar you asked for. | All remaining work | 2026-10-12: A (PO). |\n",
  structured:
    '# Plan\n## Steps\n### Detail\n- first\n  - nested\n    - deeper\n* star bullet\n1. one\n2. two\n**bold** and `code` here\n\n```ts\nconst a = 1 | 2\n```\n\n| Name | Status |\n|------|:------:|\n| IV-01 | **done** |\n| IV-02 | `open` |\n[rec] take (a)',
  mustStayPlain: '#1 priority\n2024-10-16\n1.5\n-5\n*italic*\n_x_\na ** b\nwell-known',
  wideTable:
    '| Column one is long | Column two is longer still | Column three is the longest of them all |\n|---|---|---|\n| value in column one | value in column two | value in column three, which runs on |',
  cjkTable: '| 名前 | 状態 | 備考 |\n|---|---|---|\n| 日本語のテスト | ✅ 完了 | 🚀🚀 速い |\n| 한국어 | 🙂 | emoji 👨‍👩‍👧 |',
  forty: Array.from({ length: 40 }, (_, i) => `line ${i + 1} of a forty-line body`).join('\n'),
  title300: 'T'.repeat(300),
  crlf: 'Title line\r\n\r\n- one\r\n- two\r\n[rec] (a)\r\n| A | B |\r\n|---|---|\r\n| 1 | 2 |',
  empty: '',
  titleOnly: "inbox-visual: what should 'visual' mean in the terminal inbox?",
  onlyPipe: '|',
  onlyPipes: '|\n||\n|||\n| |',
  unclosedFence: 'before\n```\nnever closed\n- not a bullet\n| a | b |',
  esc: 'plain \u001b[31mred\u001b[0m **bold \u001b[1mx** `co\u001bde`',
  osc: 'title \u001b]0;pwned\u0007 and \u001b]8;;http://x\u001b\\link\u001b]8;;\u001b\\ end',
  // body-styles.md section 6, byte for byte: the two example bodies a Manager writes (E1 answer item, R1 check-in).
  guideE1: [
    '[decision] Merge BRD-01 first (a): one merge unblocks 5 tickets.',
    '',
    '| Option | Unblocks | Risk |',
    '|---|---|---|',
    '| (a) merge BRD-01 now | 5 tickets | low |',
    '| (b) stack on dev-board-1 | 5 tickets | needs a spawn option |',
    '| (c) merge each branch | 1 per merge | slow |',
    '',
    '```diagram merge order if (a)',
    'BRD-01 ──merge──> spec ──┬─ BRD-02',
    ' (QA ok)                 ├─ BRD-03',
    '                         └─ BRD-04..06',
    '```',
    '',
    '[warning] Option (b) needs a `squad-spawn` change outside this scope.',
    '',
    'Why: (a) costs one PO merge now; (b) and (c) cost a Manager ping on every branch.',
    '',
    'Spec: [BRD-01 plan](https://github.com/acme/squad/pull/42)',
  ].join('\n'),
  guideR1: [
    '[info] All 3 tasks passed QA whitebox and blackbox. Branches are ready for your review.',
    '',
    '| Task | WB | BB |',
    '|---|---|---|',
    '| 01 item view | [ok] | [ok] |',
    '| 02 list and done | [ok] | [ok] |',
    '| 03 body styles | [ok] | [warn] |',
    '',
    '[warning] 03 passed blackbox with one note: links over 200 characters wrap.',
    '',
    '- Merge in order: `01`, `02`, `03` (all touch `hooks/po-inbox/draw.tsx`).',
    '- Evidence: `tasks/issues/NN-*/evidence.md`.',
    '- Suite: `python3 tests/run_suite.py --tz` [ok] 412 passed, 0 failed.',
    '',
    'Next: review and merge; nothing is waiting on you.',
    '',
    '[PR 12](https://github.com/acme/squad/pull/12)',
  ].join('\n'),
  // A diagram wider than a docked pane (58 columns): cut with `›` and a footer at 47 columns.
  diagramWide: [
    '```diagram merge order',
    'BRD-01 ──merge──> spec ──┬─ BRD-02 (ready)',
    ' (QA ok)                 ├─ BRD-03 (needs a second review)',
    '                         └─ BRD-04..06 (still waiting)',
    '```',
  ].join('\n'),
  // The three callout tags, and near misses that stay plain.
  tags: [
    '[decision] Merge BRD-01 first; it unblocks 5 tickets.',
    '[warning] Option (b) needs a squad-spawn change outside this scope.',
    '[info] The suite ran at 14:02 and passed (412 tests).',
    '[warning]',
    '  [info] indented',
    '[note] not a tag',
    '[Warning] wrong case',
    '[warning]x no space',
    '- [warning] inside a bullet',
    '| [decision] | in a table |',
    '|---|---|',
    '| [warning] cell | x |',
  ].join('\n'),
  // Links: label and bare; every near miss stays text.
  links: [
    'See [PR 42](https://github.com/acme/squad/pull/42) and https://example.org/a/b, then http://x.io.',
    '[](https://example.org/bare) and [a](javascript:alert(1)) and [b](file:///etc/passwd) and [c](ssh://h/x)',
    'unclosed [a](https://x.io and [a]( ) and [a]() and [a [b](https://y.io) and [a](https://x.io/a b)',
    'httpd is not a link, nor is xhttp://a.b, but (https://ok.io/path) is',
  ].join('\n'),
  // Badges: the four words, in prose and in a table; near misses stay text.
  badges: [
    'Suite [ok], lint [fail], docs [warn], e2e [skip].',
    '',
    '| Task | State |',
    '|---|---|',
    '| one | [ok] |',
    '| two | [fail] |',
    '| three | [warn] [skip] |',
    '',
    '[OK] [done] [ok](x) [ok',
  ].join('\n'),
  // Section 9.4: connectors blue, names plain, state tags filled in place, a legend row.
  relations: [
    '```diagram dependency map (A ──> B: B waits for A)',
    'BRD-01 [ok] ──> spec [ok] ──┬──> BRD-02 [ok]',
    '                            ├──> BRD-03 [warn]',
    '                            └──> BRD-04..06 [skip]',
    '```',
  ].join('\n'),
  // All callouts and all badges in one body (colour proof).
  chips: [
    '[decision] Merge BRD-01 first (a): one merge unblocks 5 tickets.',
    '[warning] Option (b) needs a change outside this scope.',
    '[info] The suite ran at 14:02.',
    '',
    '| Task | WB | BB |',
    '|---|---|---|',
    '| 01 item view | [ok] | [ok] |',
    '| 02 list and done | [ok] | [fail] |',
    '| 03 body styles | [warn] | [skip] |',
  ].join('\n'),
  rlo: '\u202eevil **bo\u202eld** `c\u202eode` | a\u202e | b |\n|---|---|\n| \u202e1 | 2 |',
}
