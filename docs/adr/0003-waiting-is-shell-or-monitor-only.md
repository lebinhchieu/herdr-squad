# `waiting` means a background shell or monitor, nothing else

Status: accepted (BRD-29)

An idle agent is `waiting` when the last pane line says `N shells still running` or `N monitors`.

**`← N agents` is not a signal.** It is in every herdr pane's footer, a constant. The first design counted it and made every idle agent waiting for good.

- A status wording sample goes in `tests/fixtures/board/panes/` before a pattern is trusted.
- The recorder polls only idle/done panes, in its own thread.
- Limit: `waiting` sees only the last pane line.

**Why hard to reverse:** the status feeds bar time (`working_s + waiting_s` = bar duration), the header dot and the idle CPU budget.
