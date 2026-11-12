import type { On } from 'claude-code'

import { back, openPane, patchUi, view } from './actions'
import { registerUi } from './ui'

// The /squads hooks, except session.start (hooks/register.tsx starts the mod there: the engine refuses two).
// Loads in every session: Chieu's plain session has no SQUAD_ROLE.
export function registerSquads(on: On): void {
  on('command.run', { command: 'squads' }, async ($) => {
    await openPane($)
    return {}
  }).catch(() => ({}))

  // Esc in a detail goes back to the list; Esc in the list closes the pane.
  on('ui.close', { id: 'squads' }, async ($, e, next) => {
    if (e.origin.kind === 'person') {
      const { ui } = await view($)
      if (ui.path.length) {
        await back($)
        return
      }
    }
    await patchUi($, { isOpen: false })
    return next(e)
  }).catch(($, e, next) => next(e))

  registerUi(on)
}
