import { execFileSync } from 'node:child_process';
import { chromium } from '@playwright/test';

const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_RADAR_UI_DOD_BASE_URL ?? 'http://127.0.0.1:5173';
const attempts = 10;
const targets = [
  'benchmark-sibur-holding-contour',
  'toir-quick-live',
  'toir-sibur',
];
let browser;

try {
  dockerCompose('up', '-d', '--build');
  await waitForApi();
  const reconciliation = dockerCompose(
    'run', '--rm', 'backend-init',
    'python', '-m', 'power_web_os.persistence', 'reconcile-radar-output-summaries',
  );
  const expected = await catalogExpectation();
  const pinnedRuns = await pinnedRunExpectation();
  browser = await chromium.launch();

  const coldOpenResults = [];
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    console.log(`Cold open ${attempt}/${attempts}.`);
    const result = await verifyCatalogOpen(browser, expected, attempt);
    coldOpenResults.push(result);
  }

  const recoveryResults = [];
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    console.log(`Recovery cycle ${attempt}/${attempts}.`);
    dockerCompose('stop', 'api');
    const context = await browser.newContext({ viewport: viewportFor(attempt) });
    await context.addInitScript(() => {
      window.localStorage.clear();
      window.localStorage.setItem('power-web-os-locale', 'en');
    });
    const page = await context.newPage();
    const errors = collectBrowserErrors(page);
    let mainNavigations = 0;
    page.on('framenavigated', (frame) => {
      if (frame === page.mainFrame()) mainNavigations += 1;
    });
    try {
      await openCatalog(page);
      await page.getByText('Demo fallback', { exact: true }).waitFor({ state: 'visible', timeout: 30_000 });
      dockerCompose('start', 'api');
      await waitForApi();
      await page.locator('.icp-profile-meta').getByText('Backend API', { exact: true }).waitFor({
        state: 'visible',
        timeout: 45_000,
      });
      await verifyCards(page, expected);
      if (mainNavigations !== 1) {
        throw new Error(`Recovery reloaded the page: main navigation count=${mainNavigations}.`);
      }
      const unexpectedErrors = errors.filter((error) => !isExpectedApiAvailabilityError(error));
      if (unexpectedErrors.length) throw new Error(unexpectedErrors.join('\n'));
      recoveryResults.push({ attempt, recovered_without_reload: true });
    } finally {
      await context.close();
      dockerCompose('start', 'api');
      await waitForApi();
    }
  }

  const apiContainerId = dockerCompose('ps', '-q', 'api').trim();
  if (!apiContainerId) throw new Error('API container is not running after recovery validation.');
  console.log('Radar catalog recovery DoD passed.');
  console.log(JSON.stringify({
    reconciliation: parseLastJson(reconciliation),
    basis_runs: Object.fromEntries(expected.map((item) => [item.radar_id, item.run_id])),
    pinned_runs: pinnedRuns,
    cold_open_passes: coldOpenResults.length,
    recovery_passes: recoveryResults.length,
    cold_open_results: coldOpenResults,
    recovery_results: recoveryResults,
  }, null, 2));
} finally {
  try {
    dockerCompose('start', 'api');
  } catch {
    // The primary failure is more useful than cleanup noise.
  }
  if (browser) await browser.close();
}

async function verifyCatalogOpen(browserInstance, expected, attempt) {
  const context = await browserInstance.newContext({ viewport: viewportFor(attempt) });
  await context.addInitScript(() => {
    window.localStorage.clear();
    window.localStorage.setItem('power-web-os-locale', 'en');
  });
  const page = await context.newPage();
  const errors = collectBrowserErrors(page);
  const eagerRequests = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (/^\/api\/radars\/[^/]+/.test(url.pathname) || url.pathname.startsWith('/api/radar-runs/')) {
      eagerRequests.push(url.pathname);
    }
  });
  try {
    await openCatalog(page);
    await page.locator('.icp-profile-meta').getByText('Backend API', { exact: true }).waitFor({
      state: 'visible',
      timeout: 30_000,
    });
    await verifyCards(page, expected);
    if (await page.getByText('Demo fallback', { exact: true }).count()) {
      throw new Error('Cold open retained demo fallback after backend catalog loaded.');
    }
    if (eagerRequests.length) {
      throw new Error(`Catalog performed eager detail/artifact requests: ${eagerRequests.join(', ')}`);
    }
    if (errors.length) throw new Error(errors.join('\n'));
    return { attempt, viewport: viewportFor(attempt), detail_requests: 0 };
  } finally {
    await context.close();
  }
}

async function openCatalog(page) {
  await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
  const catalog = page.locator('.icp-radar-catalog-list');
  if (!await catalog.isVisible().catch(() => false)) {
    const radarNav = page.getByRole('button', { name: 'ICP Radar', exact: true });
    await radarNav.waitFor({ state: 'visible', timeout: 30_000 });
    await radarNav.click();
  }
  try {
    await catalog.waitFor({ state: 'visible', timeout: 60_000 });
  } catch (error) {
    console.error(`Catalog did not open at ${page.url()}.`);
    console.error((await page.locator('body').innerText()).slice(0, 5000));
    throw error;
  }
}

async function verifyCards(page, expected) {
  for (const item of expected) {
    const card = page.locator('.card', { hasText: item.name }).first();
    await card.waitFor({ state: 'visible', timeout: 30_000 });
    const values = await card.locator('.icp-radar-list-metrics dd').allTextContents();
    for (const count of [item.candidate_count, item.review_needed_count, item.accepted_count]) {
      if (!values.includes(String(count))) {
        throw new Error(`${item.name} card does not show expected count ${count}: ${values.join(', ')}.`);
      }
    }
    if (item.run_id) {
      await card.getByText(item.run_id, { exact: true }).waitFor({ state: 'visible' });
    }
  }
}

async function catalogExpectation() {
  const response = await fetch(`${apiBaseUrl}/api/radars`);
  if (!response.ok) throw new Error(`Catalog API failed: ${response.status}.`);
  const radars = await response.json();
  const result = [];
  for (const radarId of targets) {
    const radar = radars.find((item) => item.radar_id === radarId);
    if (!radar) throw new Error(`Catalog is missing required Radar ${radarId}.`);
    const runId = radar.summary.candidate_count_run_id ?? '';
    if (runId) {
      const candidatesResponse = await fetch(`${apiBaseUrl}/api/radar-runs/${runId}/candidates`);
      if (!candidatesResponse.ok) throw new Error(`Candidates API failed for ${runId}.`);
      const candidates = await candidatesResponse.json();
      if (candidates.candidates.length !== radar.summary.candidate_count) {
        throw new Error(`${radarId} catalog/candidates mismatch.`);
      }
    }
    if (radar.summary.accepted_count + radar.summary.needs_review_count !== radar.summary.candidate_count) {
      throw new Error(`${radarId} accepted + review does not equal visible.`);
    }
    result.push({
      radar_id: radarId,
      name: radar.name,
      run_id: runId,
      candidate_count: radar.summary.candidate_count,
      accepted_count: radar.summary.accepted_count,
      review_needed_count: radar.summary.needs_review_count,
    });
  }
  const fixture = result.find((item) => item.radar_id === 'toir-sibur');
  if (!fixture || fixture.candidate_count !== 33 || fixture.accepted_count !== 0 || fixture.review_needed_count !== 33) {
    throw new Error(`TOIR / SIBUR fixture counts are not 33 = 0 + 33: ${JSON.stringify(fixture)}.`);
  }
  return result;
}

async function pinnedRunExpectation() {
  const fixtures = [
    { run_id: 'radar-run-3aa622ff-e137-48aa-9f2c-15e74f594bfc', total: 10, accepted: 3, review: 7 },
    { run_id: 'radar-run-ef74d8c0-8e19-43eb-9936-cfc0a44c383b', total: 2, accepted: 0, review: 2 },
  ];
  for (const fixture of fixtures) {
    const [runResponse, candidatesResponse] = await Promise.all([
      fetch(`${apiBaseUrl}/api/radar-runs/${fixture.run_id}`),
      fetch(`${apiBaseUrl}/api/radar-runs/${fixture.run_id}/candidates`),
    ]);
    if (!runResponse.ok || !candidatesResponse.ok) {
      throw new Error(`Pinned regression run is missing: ${fixture.run_id}.`);
    }
    const run = await runResponse.json();
    const candidates = await candidatesResponse.json();
    const accepted = candidates.candidates.filter((item) => (
      item.candidate_surface_status === 'accepted_product_candidate'
      || item.product_acceptance_status === 'product_candidate'
    )).length;
    const review = candidates.candidates.length - accepted;
    if (candidates.candidates.length !== fixture.total || accepted !== fixture.accepted || review !== fixture.review) {
      throw new Error(`Pinned run ${fixture.run_id} expected ${fixture.total}=${fixture.accepted}+${fixture.review}, got ${candidates.candidates.length}=${accepted}+${review}.`);
    }
    if (run.output?.candidate_count !== fixture.total) {
      throw new Error(`Pinned run summary mismatch for ${fixture.run_id}.`);
    }
  }
  return fixtures;
}

function collectBrowserErrors(page) {
  const errors = [];
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('pageerror', (error) => errors.push(error.message));
  return errors;
}

function isExpectedApiAvailabilityError(error) {
  return error.includes('net::ERR_CONNECTION_REFUSED') || error.includes('net::ERR_EMPTY_RESPONSE');
}

function dockerCompose(...args) {
  return execFileSync('docker', ['compose', ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

async function waitForApi() {
  const deadline = Date.now() + 90_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${apiBaseUrl}/api/health`);
      if (response.ok) return;
    } catch {
      // Container startup is expected to be briefly unavailable.
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }
  throw new Error(`Radar API was not ready within 90 seconds: ${apiBaseUrl}.`);
}

function viewportFor(attempt) {
  return attempt % 2 ? { width: 1280, height: 720 } : { width: 1366, height: 768 };
}

function parseLastJson(output) {
  const start = output.lastIndexOf('\n{');
  if (start < 0) return { raw: output.trim() };
  try {
    return JSON.parse(output.slice(start + 1));
  } catch {
    return { raw: output.trim() };
  }
}
