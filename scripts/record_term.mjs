#!/usr/bin/env node
// Record a REAL terminal session (any command, e.g. Claude Code running /hype-reel) into an asciinema v2 cast.
//
//   KEYS='[[8,"/hype-reel https://your.site"],[11,"\r"]]' node record_term.mjs <out.cast> <seconds> <cwd> -- <cmd> [args...]
//
// KEYS: [secondsFromStart, text] typed like a person. A "trust this folder" prompt is answered with Enter.
// COLS / ROWS env set the terminal size (58x30 reads well in a vertical reel). Turn the cast into video with render_term.mjs.
import fs from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let pty;
try { pty = require('@homebridge/node-pty-prebuilt-multiarch'); } catch { console.error('Needs a PTY: npm install @homebridge/node-pty-prebuilt-multiarch'); process.exit(1); }

const argv = process.argv.slice(2), sep = argv.indexOf('--');
const [out, secs, cwd] = argv.slice(0, sep), [cmd, ...args] = argv.slice(sep + 1);
if (!out || !cmd) { console.error('usage: record_term.mjs <out.cast> <seconds> <cwd> -- <cmd> [args...]'); process.exit(2); }
const COLS = +(process.env.COLS || 58), ROWS = +(process.env.ROWS || 30);
const keys = JSON.parse(process.env.KEYS || '[]');
fs.mkdirSync(cwd, { recursive: true });
const t0 = Date.now(), lines = [JSON.stringify({ version: 2, width: COLS, height: ROWS, timestamp: Math.floor(t0 / 1000) })];
const p = pty.spawn(cmd, args, { name: 'xterm-256color', cols: COLS, rows: ROWS, cwd, env: { ...process.env, FORCE_COLOR: '1' } });
let seen = '', trusted = false;
p.onData(d => {
  lines.push(JSON.stringify([(Date.now() - t0) / 1000, 'o', d]));
  seen = (seen + d).slice(-4000);
  if (!trusted && /trust/i.test(seen)) { trusted = true; setTimeout(() => p.write('\r'), 900); }
});
const type = async text => { for (const ch of text) { p.write(ch); await new Promise(r => setTimeout(r, ch === '\r' ? 0 : 55 + Math.random() * 40)); } };
(async () => {
  for (const [at, text] of keys) {
    const wait = t0 + at * 1000 - Date.now(); if (wait > 0) await new Promise(r => setTimeout(r, wait));
    await type(text);
  }
})();
setTimeout(() => {
  fs.writeFileSync(out, lines.join('\n') + '\n');
  try { p.write('\x03'); p.write('\x03'); p.kill(); } catch {}
  console.log('OK', out, lines.length - 1, 'events');
  process.exit(0);
}, +secs * 1000);
