// The plugin's one hooks module: the engine takes one per plugin and refuses two `session.start` hooks without a
// matcher. po-inbox's hooks are repeated here unchanged (hooks/po-inbox/register.tsx is no longer listed in hooks.json);
// the /squads hooks come from squads/register.tsx. One session.start starts both.
import type { Register } from 'claude-code'

import { deliverWaiting, homeOf, isActive, openPane, retryFailed, start, stop } from './po-inbox/actions'
import { registerUi } from './po-inbox/ui'
import { registerSquads } from './squads/register'
import { start as startSquads } from './squads/actions'

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    await startSquads($)
    const home = await homeOf($)
    if (home) await start($, home)
    return next(e)
  }).catch(($, e, next) => next(e))

  on('command.run', { command: 'inbox' }, async ($) => {
    if (isActive()) await openPane($)
    return {}
  }).catch(() => ({}))

  on('turn.complete', async ($, e, next) => {
    if (isActive()) await retryFailed($)
    return next(e)
  }).catch(($, e, next) => next(e))

  // A /clear ends the session id but fires no session.start: keep the timer then.
  on('session.end', async ($, e, next) => {
    if (e.reason !== 'clear') stop()
    return next(e)
  }).catch(($, e, next) => next(e))

  registerUi(on)
  registerSquads(on)
}
