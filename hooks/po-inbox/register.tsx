import type { Register } from 'claude-code'

import { deliverWaiting, homeOf, isActive, openPane, retryFailed, start, stop } from './actions'
import { registerUi } from './ui'

export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
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
}
