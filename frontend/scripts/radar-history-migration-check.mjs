import { chromium } from '@playwright/test';
import fs from 'node:fs/promises';

const baseURL = process.env.POWER_WEB_OS_RADAR_UI_DOD_BASE_URL ?? 'http://127.0.0.1:5173';
const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const radarId = 'benchmark-sibur-holding-contour';
const radarName = 'Benchmark / SIBUR holding contour';
const historicalRunId = 'radar-run-3bbf9c0f-330e-4468-8901-966a751234a8';
const outputPath = 'test-results/radar-history-migration.png';

const catalogResponse = await fetch(`${apiBaseUrl}/api/radars`);
if (!catalogResponse.ok) {
  throw new Error(`Radar catalog failed: ${catalogResponse.status}`);
}
const radar = (await catalogResponse.json()).find((item) => item.radar_id === radarId);
if (!radar) {
  throw new Error(`${radarId} is missing from the backend catalog.`);
}
const expected = {
  total: Number(radar.summary?.candidate_count ?? 0),
  accepted: Number(radar.summary?.accepted_count ?? 0),
  review: Number(radar.summary?.needs_review_count ?? 0),
  runId: String(radar.summary?.candidate_count_run_id ?? ''),
};
if (expected.total !== 91 || expected.accepted !== 84 || expected.review !== 7) {
  throw new Error(`Unexpected migrated catalog summary: ${JSON.stringify(expected)}`);
}

const historicalResponse = await fetch(
  `${apiBaseUrl}/api/radar-runs/${encodeURIComponent(historicalRunId)}/candidates`,
);
if (!historicalResponse.ok) {
  throw new Error(`Historical candidates failed: ${historicalResponse.status}`);
}
const historicalCount = (await historicalResponse.json()).candidates?.length ?? 0;
if (historicalCount !== 77) {
  throw new Error(`Expected 77 historical candidates, got ${historicalCount}.`);
}

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1366, height: 768 } });
await context.addInitScript(() => {
  window.localStorage.clear();
  window.localStorage.setItem('power-web-os-locale', 'en');
});
const page = await context.newPage();
const browserErrors = [];
page.on('console', (message) => {
  if (message.type() === 'error') browserErrors.push(message.text());
});
page.on('pageerror', (error) => browserErrors.push(error.message));

try {
  await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
  await page.getByRole('button', { name: 'ICP Radar', exact: true }).click();
  await page.getByText(radarName, { exact: true }).waitFor({ state: 'visible', timeout: 90_000 });
  const card = page.locator('.card', { hasText: radarName }).first();
  for (const count of [expected.total, expected.accepted, expected.review]) {
    await card.getByText(String(count), { exact: true }).waitFor({ state: 'visible', timeout: 90_000 });
  }
  await page.goto(`${baseURL}?runId=${encodeURIComponent(expected.runId)}`, { waitUntil: 'domcontentloaded' });
  await page.getByText(radarName, { exact: true }).waitFor({ state: 'visible', timeout: 90_000 });
  await page.locator('#radar-run-selector').waitFor({ state: 'visible', timeout: 90_000 });
  await waitForRows(page, expected.total);
  const selected = await page.locator('#radar-run-selector').inputValue();
  if (selected !== expected.runId) {
    throw new Error(`Expected selected latest run ${expected.runId}, got ${selected}.`);
  }
  const historicalOption = page.locator(`#radar-run-selector option[value="${historicalRunId}"]`);
  if (await historicalOption.count() !== 1) {
    throw new Error(`${historicalRunId} is missing from the run selector.`);
  }
  await page.goto(`${baseURL}?runId=${encodeURIComponent(historicalRunId)}`, { waitUntil: 'domcontentloaded' });
  await page.getByText(radarName, { exact: true }).waitFor({ state: 'visible', timeout: 90_000 });
  await page.getByText(historicalRunId, { exact: false }).first().waitFor({ state: 'visible', timeout: 90_000 });
  await waitForRows(page, historicalCount);
  await fs.mkdir('test-results', { recursive: true });
  await page.screenshot({ path: outputPath, fullPage: true });
  if (browserErrors.length) {
    throw new Error(`Browser errors:\n${browserErrors.join('\n')}`);
  }
  console.log(JSON.stringify({ expected, historicalRunId, historicalCount, outputPath }, null, 2));
  console.log('Radar history migration UI check passed.');
} finally {
  await context.close();
  await browser.close();
}

async function waitForRows(page, count) {
  await page.locator('.icp-radar-table-live .icp-candidate-row').first().waitFor({
    state: 'visible',
    timeout: 90_000,
  });
  await page.waitForFunction(
    (expectedCount) => document.querySelectorAll('.icp-radar-table-live .icp-candidate-row').length === expectedCount,
    count,
    { timeout: 90_000 },
  );
}
