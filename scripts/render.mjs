#!/usr/bin/env node
// Render a built hype reel page to an MP4, frame by frame (every frame is exact, no dropped frames).
//
//   node render.mjs reel.html out.mp4 [--fps 30] [--audio voice.wav] [--from 0] [--to 12.5] [--crf 18]
//   node render.mjs reel.html --stills 0.5,2,4.2 [--outdir stills]     (quick PNG checks)
//
// The page's own audio (storyboard "audio") is muxed in automatically unless --audio is given.
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import ffmpegStatic from 'ffmpeg-static';
import { launch } from './chrome.mjs';

const args = process.argv.slice(2);
const flag = (k, d) => { const i = args.indexOf('--' + k); return i < 0 ? d : args[i + 1]; };
const pos = args.filter((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
const [htmlFile, outFile] = pos;
if (!htmlFile) { console.error('usage: render.mjs reel.html out.mp4 [--fps 30] [--audio f] [--from s] [--to s] | --stills t1,t2'); process.exit(2); }
const FFMPEG = process.env.FFMPEG || ffmpegStatic || 'ffmpeg';

const browser = await launch();
try {
  const page = await browser.newPage();
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('CONSOLE', m.text()); });
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.resolve(htmlFile)).href + '?render=1', { waitUntil: 'networkidle0', timeout: 120000 });
  await page.waitForFunction('window.__hype', { timeout: 60000 });
  const info = await page.evaluate(async () => { await window.__hype.ready; const h = window.__hype; return { W: h.W, H: h.H, fps: h.fps, duration: h.duration, audioPath: h.audioPath, scenes: h.scenes }; });
  await page.setViewport({ width: info.W, height: info.H, deviceScaleFactor: 1 });
  const cdp = await page.createCDPSession();
  const grab = async (format = 'jpeg') => Buffer.from((await cdp.send('Page.captureScreenshot', { format, quality: format === 'jpeg' ? 92 : undefined, optimizeForSpeed: true, captureBeyondViewport: false })).data, 'base64');

  if (flag('stills')) {
    const dir = flag('outdir', 'stills'); fs.mkdirSync(dir, { recursive: true });
    for (const t of String(flag('stills')).split(',').map(Number)) {
      await page.evaluate(t => window.__hype.seek(t), t);
      const f = path.join(dir, `t${t.toFixed(2)}.png`); fs.writeFileSync(f, await grab('png')); console.log(f);
    }
  } else {
    const fps = +flag('fps', info.fps), from = +flag('from', 0), to = Math.min(+flag('to', info.duration), info.duration);
    const frames = Math.round((to - from) * fps);
    const audio = flag('audio', info.audioPath);
    const ff = [
      '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      ...(audio ? ['-ss', String(from), '-i', audio] : []),
      '-c:v', 'libx264', '-preset', 'medium', '-crf', flag('crf', '18'), '-pix_fmt', 'yuv420p', '-color_range', 'tv', '-r', String(fps),
      ...(audio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []), '-movflags', '+faststart', outFile || 'reel.mp4',
    ];
    const proc = spawn(FFMPEG, ff, { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise((res, rej) => proc.on('close', c => c ? rej(new Error('ffmpeg exited ' + c)) : res()));
    const t0 = Date.now();
    for (let i = 0; i < frames; i++) {
      await page.evaluate(t => window.__hype.seek(t), from + i / fps);
      const buf = await grab();
      if (!proc.stdin.write(buf)) await new Promise(r => proc.stdin.once('drain', r));
      if (i % fps === 0) process.stdout.write(`\r${i}/${frames} frames  ${((Date.now() - t0) / 1000).toFixed(0)} s`);
    }
    proc.stdin.end(); await done;
    console.log(`\nOK ${outFile || 'reel.mp4'}  ${info.W}x${info.H} ${fps} fps, ${(to - from).toFixed(1)} s${audio ? ', with audio' : ''}`);
  }
} finally { await browser.close(); }
