import { chromium } from '@playwright/test';

const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_RADAR_UI_DOD_BASE_URL ?? 'http://127.0.0.1:5173';
const radarId = process.env.POWER_WEB_OS_RADAR_SETTINGS_RADAR_ID ?? 'benchmark-sibur-holding-contour';
const attempts = 10;
const browser = await chromium.launch();
const results = [];

try {
  await waitForApi();
  const detailResponse = await fetch(`${apiBaseUrl}/api/radars/${radarId}`);
  const detailBytes = Buffer.byteLength(await detailResponse.text());
  const historyResponse = await fetch(`${apiBaseUrl}/api/radars/${radarId}/runs?limit=20`);
  const historyBytes = Buffer.byteLength(await historyResponse.text());
  if (!detailResponse.ok || detailBytes > 250_000) throw new Error(`Detail payload is ${detailBytes} bytes.`);
  if (!historyResponse.ok || historyBytes > 250_000) throw new Error(`History payload is ${historyBytes} bytes.`);

  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const viewport = attempt % 2 ? { width: 1280, height: 720 } : { width: 1366, height: 768 };
    const context = await browser.newContext({ viewport });
    await context.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('power-web-os-locale', 'en');
    });
    const page = await context.newPage();
    const detailRequestsBeforeOpen = [];
    const errors = [];
    let radarOpened = false;
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (!radarOpened && /^\/api\/radars\/[^/]+$/.test(url.pathname)) detailRequestsBeforeOpen.push(url.pathname);
    });
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('requestfailed', (request) => errors.push(
      `${request.failure()?.errorText ?? 'request failed'} ${request.url()}`,
    ));
    try {
      await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
      const card = page.getByText('Benchmark / SIBUR holding contour', { exact: true }).first();
      await card.waitFor({ state: 'visible', timeout: 30_000 });
      if (detailRequestsBeforeOpen.length) {
        throw new Error(`Catalog eagerly requested details: ${detailRequestsBeforeOpen.join(', ')}`);
      }
      radarOpened = true;
      await card.click();
      await page.locator('.icp-radar-tabs button').filter({ hasText: 'Settings' }).click();
      try {
        await page.getByText('Current active definition', { exact: true }).waitFor({ state: 'visible', timeout: 30_000 });
      } catch (error) {
        console.error((await page.locator('body').innerText()).slice(0, 5000));
        throw error;
      }
      await page.getByText('Account qualification rules', { exact: true }).waitFor({ state: 'visible' });
      await page.getByText('Intent signals', { exact: true }).waitFor({ state: 'visible' });
      const body = await page.locator('body').innerText();
      if (body.includes('Radar settings could not be loaded')) throw new Error('Definition load failed.');
      if (body.includes('Demo fallback')) throw new Error('API mode silently rendered demo fallback.');
      const detail = await (await fetch(`${apiBaseUrl}/api/radars/${radarId}`)).json();
      const definition = detail.active_definition?.definition_payload;
      const ruleCount = definition?.account_qualification?.rule_group?.rules?.length ?? 0;
      const signalCount = definition?.intent_signals?.length ?? 0;
      const sourceCount = definition?.global_search_policy?.sources?.length ?? 0;
      if (ruleCount !== 2 || signalCount !== 3 || sourceCount !== 3) {
        throw new Error(`Expected 2/3/3 settings, got ${ruleCount}/${signalCount}/${sourceCount}.`);
      }
      const layout = await page.evaluate(() => {
        const bodyOverflow = document.documentElement.scrollHeight > window.innerHeight + 2;
        const rects = Array.from(document.querySelectorAll('.icp-settings-grid > *')).map((element) => {
          const rect = element.getBoundingClientRect();
          return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom };
        });
        const overlaps = rects.some((left, index) => rects.slice(index + 1).some((right) => (
          Math.min(left.right, right.right) - Math.max(left.left, right.left) > 1
          && Math.min(left.bottom, right.bottom) - Math.max(left.top, right.top) > 1
        )));
        return { bodyOverflow, overlaps };
      });
      if (layout.bodyOverflow || layout.overlaps) throw new Error(`Invalid settings layout: ${JSON.stringify(layout)}`);
      if (errors.length) throw new Error(errors.join('\n'));
      results.push({ attempt, viewport, rule_count: ruleCount, signal_count: signalCount, source_count: sourceCount });
    } finally {
      await context.close();
    }
  }
  console.log('Radar settings lazy-loading DoD passed.');
  console.log(JSON.stringify({
    radar_id: radarId,
    cold_open_passes: results.length,
    detail_bytes: detailBytes,
    history_bytes: historyBytes,
    catalog_detail_requests_before_open: 0,
    results,
  }, null, 2));
} finally {
  await browser.close();
}

async function waitForApi() {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/health`);
      if (response.ok) return;
    } catch {
      // The container may be started while the application is still booting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }
  throw new Error(`Radar API was not ready within 60 seconds: ${apiBaseUrl}.`);
}
