// Find a local Chrome / Edge / Chromium and launch it headless with puppeteer-core.
import fs from 'node:fs';
import puppeteer from 'puppeteer-core';

const CANDIDATES = {
  win32: [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    `${process.env.LOCALAPPDATA}/Google/Chrome/Application/chrome.exe`,
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  ],
  darwin: [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
  ],
  linux: ['/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser', '/snap/bin/chromium', '/usr/bin/microsoft-edge'],
};

export function findChrome() {
  if (process.env.CHROME_PATH && fs.existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
  const hit = (CANDIDATES[process.platform] || CANDIDATES.linux).find(p => p && fs.existsSync(p));
  if (!hit) throw new Error('No Chrome/Edge/Chromium found. Install one or set CHROME_PATH.');
  return hit;
}

export function launch(extra = {}) {
  return puppeteer.launch({
    executablePath: findChrome(),
    headless: true,
    args: ['--hide-scrollbars', '--force-color-profile=srgb', '--font-render-hinting=none', '--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required'],
    ...extra,
  });
}
