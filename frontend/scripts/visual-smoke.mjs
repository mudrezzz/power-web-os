import { chromium } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'vite';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, '..');
const repoRoot = path.resolve(frontendRoot, '..');
const outputRoot = path.resolve(repoRoot, 'docs', 'qa', 'screenshots', 'visual-smoke');
const port = Number(process.env.POWER_WEB_OS_VISUAL_PORT ?? 4175);
const baseURL = `http://127.0.0.1:${port}`;

const viewports = [
  { name: '1280x720', width: 1280, height: 720 },
  { name: '1366x768', width: 1366, height: 768 },
];

const screens = [
  { name: 'icp-radar', nav: null, expectedText: 'ICP Radar' },
  { name: 'accounts', nav: 'Accounts', expectedText: 'Accounts' },
  { name: 'account-map', nav: 'Account Map', expectedText: 'Account Map' },
  { name: 'access-plans', nav: 'Access Plans', expectedText: 'Access Plans' },
  { name: 'playbook', nav: 'Playbook', expectedText: 'Playbook' },
];

await mkdir(outputRoot, { recursive: true });

const server = await createServer({
  root: frontendRoot,
  logLevel: 'warn',
  server: {
    host: '127.0.0.1',
    port,
    strictPort: true,
  },
});

let browser;

try {
  await server.listen();
  await waitForServer();

  browser = await chromium.launch();

  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: {
        width: viewport.width,
        height: viewport.height,
      },
    });
    await context.addInitScript(() => {
      window.localStorage.setItem('power-web-os-locale', 'en');
    });
    const page = await context.newPage();
    await page.goto(baseURL, { waitUntil: 'domcontentloaded' });

    for (const screen of screens) {
      if (screen.nav) {
        await page.getByRole('button', { name: screen.nav, exact: true }).click();
      }
      await page.getByText(screen.expectedText, { exact: false }).first().waitFor({ state: 'visible' });
      await assertNotBlank(page, screen.name);
      await page.screenshot({
        animations: 'disabled',
        fullPage: false,
        path: path.join(outputRoot, `${screen.name}-${viewport.name}.png`),
      });
    }

    await context.close();
  }

  console.log(`Visual smoke screenshots written to ${path.relative(repoRoot, outputRoot)}`);
} finally {
  if (browser) {
    await browser.close();
  }
  await server.close();
}

async function waitForServer() {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseURL}/demo/icp_radar.json`);
      if (response.ok) {
        return;
      }
    } catch {
      // Vite is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for ${baseURL}`);
}

async function assertNotBlank(page, screenName) {
  const bodyText = await page.locator('body').innerText();
  if (bodyText.trim().length < 80) {
    throw new Error(`Visual smoke detected a blank or under-rendered ${screenName} screen.`);
  }
}
