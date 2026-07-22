import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_HANDOFF_UI_BASE_URL ?? 'http://127.0.0.1:5173';
const radarId = 'benchmark-sibur-holding-contour';
const runId = 'radar-run-fixture-power-web-handoff';
const acceptedId = 'ao-sibur-him-prom-demo';
const reviewId = 'ao-permskie-poliefiry-demo';

await waitForApi();
console.log('API ready; validating deterministic policy and preflight contracts.');
const runsBefore = await radarRunCount();
const policy = await json(`${apiBaseUrl}/api/radars/${radarId}/power-web-policy`);
if (policy.product_bindings.length !== 2) throw new Error(`Expected 2 products, got ${policy.product_bindings.length}.`);
const candidates = await json(`${apiBaseUrl}/api/radar-runs/${runId}/candidates`);
if (candidates.candidates.length !== 2) throw new Error(`Expected 2 fixture candidates, got ${candidates.candidates.length}.`);
const allPreflight = await json(`${apiBaseUrl}/api/radars/${radarId}/power-web-handoff/preflight?source_candidate_run_id=${runId}&candidate_id=${acceptedId}`);
if (!allPreflight.ready || allPreflight.role_demand_count !== 14) {
  throw new Error(`All-product preflight must be ready with 14 roles: ${JSON.stringify(allPreflight)}`);
}
const firstProduct = policy.product_bindings[0].product_id;
const subsetPreflight = await json(`${apiBaseUrl}/api/radars/${radarId}/power-web-handoff/preflight?source_candidate_run_id=${runId}&candidate_id=${acceptedId}&product_ids=${encodeURIComponent(firstProduct)}`);
if (!subsetPreflight.ready || subsetPreflight.role_demand_count !== 8) {
  throw new Error(`SmartDiagnostics preflight must contain 8 roles: ${JSON.stringify(subsetPreflight)}`);
}
const blockedReview = await json(`${apiBaseUrl}/api/radars/${radarId}/power-web-handoff/preflight?source_candidate_run_id=${runId}&candidate_id=${reviewId}`);
if (blockedReview.ready || !blockedReview.blockers.includes('review_needed_acknowledgement_required')) {
  throw new Error(`Review-needed preflight was not blocked: ${JSON.stringify(blockedReview)}`);
}

const browser = await chromium.launch();
const results = [];
try {
  for (const scenario of [
    { locale: 'ru', viewport: { width: 1280, height: 720 }, candidateId: acceptedId, review: false },
    { locale: 'en', viewport: { width: 1366, height: 768 }, candidateId: reviewId, review: true },
  ]) {
    console.log(`Validating ${scenario.locale} UI at ${scenario.viewport.width}x${scenario.viewport.height} for ${scenario.candidateId}.`);
    const context = await browser.newContext({ viewport: scenario.viewport });
    await context.addInitScript((locale) => {
      window.localStorage.clear();
      window.localStorage.setItem('power-web-os-locale', locale);
    }, scenario.locale);
    const page = await context.newPage();
    const errors = [];
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(`${baseURL}/?runId=${runId}&candidateId=${scenario.candidateId}`, { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="power-web-handoff-preflight"], [data-testid="power-web-handoff-ready"]').first().waitFor({ timeout: 45_000 });
    const ready = page.locator('[data-testid="power-web-handoff-ready"]');
    if (!await ready.count()) {
      if (scenario.review) {
        await page.locator('.power-web-review-ack input').check();
      }
      await page.locator('[data-testid="prepare-power-web"]').click();
      await ready.waitFor({ timeout: 30_000 });
    }
    const roleCount = await page.locator('.power-web-role-list > div').count();
    if (roleCount !== 14) throw new Error(`Expected 14 rendered roles, got ${roleCount}.`);
    const currentUrl = new URL(page.url());
    if (currentUrl.searchParams.get('runId') !== runId
      || currentUrl.searchParams.get('candidateId') !== scenario.candidateId
      || !currentUrl.searchParams.get('handoffId')) {
      throw new Error(`Incomplete handoff URL: ${currentUrl.toString()}`);
    }
    const layout = await page.evaluate(() => ({
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
      bodyOverflow: document.documentElement.scrollHeight > window.innerHeight + 2,
    }));
    if (layout.horizontalOverflow || layout.bodyOverflow) throw new Error(`Invalid layout: ${JSON.stringify(layout)}`);
    if (errors.length) throw new Error(errors.join('\n'));
    results.push({ ...scenario, role_count: roleCount, handoff_id: currentUrl.searchParams.get('handoffId') });
    await context.close();
  }
} finally {
  await browser.close();
}

const runsAfter = await radarRunCount();
if (runsBefore !== runsAfter) throw new Error(`Handoff created Radar runs: before=${runsBefore}, after=${runsAfter}.`);
const evidence = {
  validation_status: 'PASS', radar_id: radarId, candidate_run_id: runId,
  products: 2, all_roles: 14, subset_roles: 8, runs_before: runsBefore, runs_after: runsAfter, results,
};
await mkdir(new URL('../test-results/', import.meta.url), { recursive: true });
await writeFile(new URL('../test-results/power-web-handoff.json', import.meta.url), `${JSON.stringify(evidence, null, 2)}\n`);
console.log('Power Web handoff DoD passed.');
console.log(JSON.stringify(evidence, null, 2));

async function json(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${url}: ${await response.text()}`);
  return response.json();
}

async function radarRunCount() {
  const discovery = await json(`${apiBaseUrl}/api/radars/${radarId}/runs?limit=100`);
  const signal = await json(`${apiBaseUrl}/api/radars/${radarId}/signal-monitoring-runs?limit=100`);
  return discovery.length + signal.length;
}

async function waitForApi() {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/health`);
      if (response.ok) return;
    } catch {}
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }
  throw new Error(`API did not become ready at ${apiBaseUrl}.`);
}
