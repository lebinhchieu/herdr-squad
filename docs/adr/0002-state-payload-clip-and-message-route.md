# `/state` and `/events` clip row text; full text by `GET /message/<id>`

Status: superseded by 0009 (was: accepted (BRD-32))

Rows carry 140 characters and `text_clipped: true`. The full text comes from `GET /message/<msg_id>?token=`, plain text.

- The clip applies only when the id passes the route's regex.
- Checks run in this order: Host/Origin, token, id regex, log lookup. The id is never joined into a path.
- The page fetches on "show more", caches by id, and keeps the button if the fetch fails, so a click retries.
- `/state` top-level keys are fixed (`now, iterations, iteration, selected_iteration, pods, columns, rows, bars, tasks, needs_you`). Additions are allowed; renames and removals need the Tech Lead's DECISION.

**Why surprising:** `/state` is not the whole message, and the token never appears in a body.
