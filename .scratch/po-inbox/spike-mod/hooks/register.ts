import type { Register } from 'claude-code'
const LOG = '/tmp/po-spike/log.txt'
async function log($: any, msg: string) {
  await $.process.run(['tee', '-a', LOG], { stdin: new Date().toISOString() + ' ' + msg + '\n' })
}
async function sub($: any, text: string, tag: string) {
  const t0 = Date.now()
  try {
    const r = await $.prompt.submit({ text })
    await log($, 'S1 ' + tag + ' resolved ' + JSON.stringify(r) + ' after ' + (Date.now() - t0) + 'ms')
  } catch (x) { await log($, 'S1 ' + tag + ' REJECTED ' + String(x)) }
}
export const register: Register = (on) => {
  on('session.start', async ($, e, next) => {
    await log($, 'S2 env SQUAD_ROLE=' + String(await $.env.get('SQUAD_ROLE')) + ' SCOPE_DIR=' + String(await $.env.get('SCOPE_DIR')) + ' GOAL_DIR=' + String(await $.env.get('GOAL_DIR')) + ' plugin.root=' + $.plugin.root)
    const r = await $.process.run([$.plugin.root + '/bin/squad-inbox', 'answer', 'E1', '--source', 'pane'], { stdin: 'line1\nq"uo`te|é😀\r\nx' })
    await log($, 'S4 run exit=' + r.exitCode + ' out=' + JSON.stringify(r.stdout))
    const st = await $.fs.stat('/tmp/po-spike/watch.txt').catch((x: any) => 'ERR ' + x)
    await log($, 'S4 stat1=' + JSON.stringify(st))
    const pe = await $.process.run(['printenv', 'SQUAD_ROLE', 'SCOPE_DIR', 'GOAL_DIR', 'SQUAD_INBOX_NOW'])
    await log($, 'S2 process.run printenv exit=' + pe.exitCode + ' out=' + JSON.stringify(pe.stdout))
    const mode = await $.env.get('SPIKE_REDELIVER')
    if (mode === 'void') { void sub($, 'S1-R: reply with exactly the word ROMEO', 'R-void') }
    if (mode === 'timer') { $.clock.after(500, () => { void sub($, 'S1-R: reply with exactly the word ROMEO', 'R-timer') }) }
    await $.command.register({ name: 'spike', description: 'S1' }); await $.command.register({ name: 'spikeb', description: 'S1b' })
    $.clock.every(1000, () => { void (async () => {
      const s = await $.fs.stat('/tmp/po-spike/watch.txt').catch(() => null)
      await log($, 'tick mtime=' + (s && s.mtimeMs))
    })() })
    return next(e)
  })
  on('command.run', { command: 'spike' }, async ($, e) => {
    await log($, 'S1 command run; scheduling submit in 1s')
    $.clock.after(1000, () => { void sub($, 'S1-A: reply with exactly the word ALPHA', 'A') })
    return { text: 'spike ran' }
  })
  on('command.run', { command: 'spikeb' }, async ($, e) => {
    await log($, 'S1b command run; scheduling submit in 6s (during a turn)')
    $.clock.after(6000, () => { void sub($, 'S1-B: reply with exactly the word BRAVO', 'B') })
    return { text: 'spikeb ran' }
  })
  on('command.run', { command: 'spike2' }, async ($, e) => {
    return { text: 'x' }
  })
  on('turn.start', async ($, e, next) => { await log($, 'turn.start'); return next(e) })
  on('turn.complete', async ($, e, next) => { await log($, 'turn.complete'); return next(e) })
}
