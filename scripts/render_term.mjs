#!/usr/bin/env node
// Replay a recorded cast in a real terminal emulator (xterm.js) and render it frame by frame to an MP4 (1000 px wide window).
//
//   node render_term.mjs <session.cast> <out.mp4> [--fs 26] [--title "Terminal — claude"] [--to 40]
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import ffmpegStatic from 'ffmpeg-static';
import { launch } from './chrome.mjs';

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf('--' + k); return i < 0 ? d : args[i + 1]; };
const [cast, out] = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
if (!cast || !out) { console.error('usage: render_term.mjs <session.cast> <out.mp4> [--fs 26] [--title t] [--to s]'); process.exit(2); }
const FPS = 30;
const page = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'assets', 'term.html');
const castData = fs.readFileSync(cast);
// tiny local server: term.html + the cast (fetch() can't read file:// URLs)
const srv = http.createServer((q, r) => { const u = q.url.split('?')[0]; if (u === '/term.html') { r.writeHead(200, { 'content-type': 'text/html' }); r.end(fs.readFileSync(page)); } else if (u === '/session.cast') { r.writeHead(200); r.end(castData); } else { r.writeHead(404); r.end(); } });
await new Promise(r => srv.listen(0, '127.0.0.1', r));
const port = srv.address().port;
const b = await launch();
try {
  const p = await b.newPage();
  await p.setViewport({ width: 1000, height: 1600, deviceScaleFactor: 1 });
  await p.goto(`http://127.0.0.1:${port}/term.html?cast=/session.cast&fs=${flag('fs', 26)}&title=${encodeURIComponent(flag('title', 'Terminal'))}`, { waitUntil: 'load' });
  await p.waitForFunction('window.__term', { timeout: 60000 });
  const duration = Math.min(+flag('to', 1e9), await p.evaluate(() => window.__term.duration));
  const size = await p.evaluate(() => window.__term.size());
  const W = size.w + (size.w % 2), H = size.h + (size.h % 2);
  const ff = spawn(process.env.FFMPEG || ffmpegStatic, ['-y', '-v', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const n = Math.ceil(duration * FPS) + FPS;
  for (let k = 0; k < n; k++) {
    await p.evaluate(t => window.__term.seek(t), k / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 94, clip: { x: 0, y: 0, width: W, height: H } });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (k % (FPS * 5) === 0) process.stdout.write(`\r${k}/${n} frames`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log(`\nOK ${out}  ${W}x${H}, ${(n / FPS).toFixed(1)} s  (aspect ${(W / H).toFixed(3)} for the clip scene)`);
} finally { await b.close(); srv.close(); }
