import { chromium } from '@playwright/test';
import { createServer } from 'vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(__dirname, '..');
const startVite = process.env.POWER_WEB_OS_RADAR_UI_DOD_START_VITE === '1';
const port = Number(process.env.POWER_WEB_OS_RADAR_UI_DOD_PORT ?? 5173);
const iterations = Number(process.env.POWER_WEB_OS_RADAR_UI_DOD_ITERATIONS ?? 10);
const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_RADAR_UI_DOD_BASE_URL ?? `http://127.0.0.1:${port}`;
const benchmarkRadarId = 'benchmark-sibur-holding-contour';
const benchmarkName = 'Benchmark / SIBUR holding contour';
const storageKey = 'power-web-os-icp-radar-config-overrides';
const uiWaitMs = 90000;

let server;
let browser;

try {
  if (startVite) {
    console.log(`Starting dedicated Vite DoD server on ${baseURL}.`);
    server = await createServer({
      root: frontendRoot,
      logLevel: 'warn',
      server: {
        host: '127.0.0.1',
        port,
        strictPort: true,
      },
    });
    await server.listen();
  } else {
    console.log(`Using existing frontend DoD target on ${baseURL}.`);
  }
  await waitForServer();

  console.log('Checking backend benchmark radar readiness.');
  const expected = await benchmarkExpectationFromBackend();
  console.log(`Backend benchmark run: ${expected.runId}; candidates=${expected.total}, accepted=${expected.accepted}, review=${expected.review}.`);

  browser = await chromium.launch();
  const results = [];
  for (let iteration = 1; iteration <= iterations; iteration += 1) {
    console.log(`DoD iteration ${iteration}/${iterations}.`);
    await runIteration(browser, expected, iteration);
    results.push({
      iteration,
      radar_id: benchmarkRadarId,
      run_id: expected.runId,
      candidates: expected.total,
      accepted: expected.accepted,
      review_needed: expected.review,
    });
  }

  console.log('Radar benchmark UI DoD passed.');
  console.log(JSON.stringify({ iterations, results }, null, 2));
} finally {
  if (browser) {
    await browser.close();
  }
  if (server) {
    await server.close();
  }
}

async function runIteration(browserInstance, expected, iteration) {
  const browserErrors = [];
  const context = await browserInstance.newContext({ viewport: { width: 1366, height: 768 } });
  await context.addInitScript(({ storageKey: injectedStorageKey, benchmarkRadarId: injectedRadarId, benchmarkName: injectedName }) => {
    window.localStorage.clear();
    window.localStorage.setItem('power-web-os-locale', 'en');
    window.localStorage.setItem(injectedStorageKey, JSON.stringify({
      [injectedRadarId]: {
        override_type: 'deleted',
        saved_at: new Date(0).toISOString(),
        radar: {
          radar_id: injectedRadarId,
          name: injectedName,
          status: 'configured',
          owner: 'ABM Research',
          profile: {
            icp_profile: injectedName,
            product: '',
            segment: '',
            scope: '',
          },
          summary: {
            cadence: 'manual',
            last_run: 'not_run',
            candidate_count: 0,
            needs_review_count: 0,
            accepted_count: 0,
            run_mode: 'benchmark',
          },
          definition: {},
          artifact_path: null,
        },
      },
    }));
  }, { storageKey, benchmarkRadarId, benchmarkName });

  const page = await context.newPage();
  page.on('console', (message) => {
    if (message.type() === 'error') {
      const text = message.text();
      browserErrors.push(text);
      console.log(`browser console error [${iteration}]: ${text}`);
    }
  });
  page.on('pageerror', (error) => {
    browserErrors.push(error.message);
    console.log(`browser page error [${iteration}]: ${error.message}`);
  });

  try {
    await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: 'ICP Radar', exact: true }).click();
    await page.getByText(benchmarkName, { exact: true }).waitFor({ state: 'visible', timeout: uiWaitMs });
    await page.locator('.icp-profile-meta').getByText('Backend API', { exact: true }).waitFor({ state: 'visible', timeout: uiWaitMs });
    await page.getByText('Backend radar kept', { exact: false }).waitFor({ state: 'visible', timeout: uiWaitMs });
    if (await page.getByText('Demo fallback', { exact: true }).count()) {
      throw new Error('Demo fallback is visible while backend benchmark radar is expected.');
    }

    const benchmarkCard = page.locator('.card', { hasText: benchmarkName }).first();
    await benchmarkCard.getByText(String(expected.total), { exact: true }).waitFor({ state: 'visible', timeout: uiWaitMs });
    await benchmarkCard.getByText(String(expected.review), { exact: true }).waitFor({ state: 'visible' });
    await benchmarkCard.getByText(String(expected.accepted), { exact: true }).waitFor({ state: 'visible' });
    await benchmarkCard.click();

    await page.locator('.icp-radar-table-live .icp-candidate-row').first().waitFor({ state: 'visible', timeout: uiWaitMs });
    const candidateRows = await page.locator('.icp-radar-table-live .icp-candidate-row').count();
    if (candidateRows !== expected.total) {
      throw new Error(`Expected ${expected.total} visible live candidate rows, got ${candidateRows}.`);
    }
    await page.getByText(`${expected.total} candidates`, { exact: true }).waitFor({ state: 'visible' });
    await page.getByText(`${expected.accepted} accepted/product`, { exact: true }).waitFor({ state: 'visible' });
    await page.getByText(`${expected.review} review-needed`, { exact: true }).waitFor({ state: 'visible' });
    await page.getByText(expected.runId, { exact: false }).waitFor({ state: 'visible' });
    for (let index = 0; index < expected.candidates.length; index += 1) {
      const candidate = expected.candidates[index];
      const row = page.locator('.icp-radar-table-live .icp-candidate-row').nth(index);
      await row.click();
      await page.getByRole('button', { name: 'Open details', exact: true }).click();
      await page.getByText(candidate.legal_name, { exact: true }).first().waitFor({ state: 'visible', timeout: uiWaitMs });
      await page.getByText(candidate.reason, { exact: false }).first().waitFor({ state: 'visible', timeout: uiWaitMs });
      await page.getByRole('button', { name: 'Sources', exact: true }).click();
      const source = candidate.sources[0];
      await page.getByText(source.title, { exact: false }).first().waitFor({ state: 'visible', timeout: uiWaitMs });
      await page.getByText(source.source_type, { exact: false }).first().waitFor({ state: 'visible', timeout: uiWaitMs });
      await page.getByRole('button', { name: 'Back to found accounts', exact: true }).click();
      await page.locator('.icp-radar-table-live .icp-candidate-row').first().waitFor({ state: 'visible', timeout: uiWaitMs });
    }
    if (browserErrors.length > 0) {
      throw new Error(`Browser console/page errors during iteration ${iteration}:\n${browserErrors.join('\n')}`);
    }
  } finally {
    await context.close();
  }
}

async function benchmarkExpectationFromBackend() {
  const response = await fetch(`${apiBaseUrl}/api/radars`);
  if (!response.ok) {
    throw new Error(`Radar API is not available on ${apiBaseUrl}: ${response.status}.`);
  }
  const radars = await response.json();
  if (radars.length < 7) {
    throw new Error(`Backend seed is incomplete: expected at least 7 radars, got ${radars.length}.`);
  }
  const radar = radars.find((item) => item.radar_id === benchmarkRadarId);
  if (!radar) {
    throw new Error(`Backend did not return ${benchmarkRadarId}.`);
  }
  if (radar.latest_run?.status !== 'completed' || !radar.latest_run?.output) {
    throw new Error(`${benchmarkRadarId} has no completed latest run with output.`);
  }
  const candidatesResponse = await fetch(`${apiBaseUrl}/api/radar-runs/${encodeURIComponent(radar.latest_run.run_id)}/candidates`);
  if (!candidatesResponse.ok) {
    throw new Error(`Candidates endpoint failed for ${radar.latest_run.run_id}: ${candidatesResponse.status}.`);
  }
  const candidatesPayload = await candidatesResponse.json();
  const candidates = Array.isArray(candidatesPayload.candidates) ? candidatesPayload.candidates : [];
  const accepted = candidates.filter((candidate) => (
    candidate.candidate_surface_status === 'accepted_product_candidate'
    || candidate.product_acceptance_status === 'product_candidate'
  )).length;
  const review = candidates.filter((candidate) => (
    candidate.candidate_surface_status === 'review_needed_candidate'
    || candidate.product_acceptance_status === 'review_required'
  )).length;
  const sourcesByRef = new Map((Array.isArray(candidatesPayload.sources) ? candidatesPayload.sources : [])
    .map((source) => [source.evidence_ref, source]));
  const expected = {
    runId: radar.latest_run.run_id,
    total: candidates.length,
    accepted,
    review,
    candidates: candidates.map((candidate) => ({
      candidate_id: candidate.candidate_id,
      legal_name: candidate.legal_name,
      reason: candidate.candidate_surface_reason
        || candidate.public_projection_reason
        || candidate.product_acceptance_reason
        || candidate.upstream_reason
        || 'Review-needed',
      sources: candidateSources(candidate, sourcesByRef),
    })),
  };
  const duplicateIds = duplicateCandidateIds(candidates);
  if (duplicateIds.length) {
    throw new Error(`Backend candidate surface has duplicate candidate ids: ${duplicateIds.join(', ')}.`);
  }
  const emptyEvidence = candidates.filter((candidate) => !candidateHasPublicEvidence(candidate, sourcesByRef));
  if (emptyEvidence.length) {
    throw new Error(`Backend candidate surface has empty provenance: ${emptyEvidence.map((item) => item.legal_name).join(', ')}.`);
  }
  if (expected.total !== 12 || expected.accepted !== 3 || expected.review !== 9) {
    throw new Error(`Backend candidate surface does not match DoD: ${JSON.stringify(expected)}.`);
  }
  assertSummaryMatchesBackend(radar, expected);
  return expected;
}

function candidateSources(candidate, sourcesByRef) {
  const refs = [
    ...(Array.isArray(candidate.evidence_refs) ? candidate.evidence_refs : []),
    ...(Array.isArray(candidate.upstream_source_refs) ? candidate.upstream_source_refs : []),
  ].filter(Boolean);
  const sources = refs.map((ref) => sourcesByRef.get(ref)).filter(Boolean);
  if (sources.length) {
    return sources;
  }
  return [{
    title: candidate.legal_name,
    source_type: 'diagnostic',
  }];
}

function duplicateCandidateIds(candidates) {
  const seen = new Set();
  const duplicates = new Set();
  for (const candidate of candidates) {
    const id = String(candidate.candidate_id ?? '').trim();
    if (!id) {
      continue;
    }
    if (seen.has(id)) {
      duplicates.add(id);
    }
    seen.add(id);
  }
  return Array.from(duplicates).sort();
}

function candidateHasPublicEvidence(candidate, sourcesByRef) {
  const refs = [
    ...(Array.isArray(candidate.evidence_refs) ? candidate.evidence_refs : []),
    ...(Array.isArray(candidate.upstream_source_refs) ? candidate.upstream_source_refs : []),
  ].filter(Boolean);
  if (refs.some((ref) => sourcesByRef.has(ref))) {
    return true;
  }
  return Boolean(
    candidate.candidate_surface_reason
    || candidate.public_projection_reason
    || candidate.product_acceptance_reason
    || candidate.upstream_reason
  );
}

function assertSummaryMatchesBackend(radar, expected) {
  const summary = radar.summary ?? {};
  const actual = {
    total: Number(summary.candidate_count ?? 0),
    accepted: Number(summary.accepted_count ?? 0),
    review: Number(summary.needs_review_count ?? 0),
  };
  if (actual.total !== expected.total || actual.accepted !== expected.accepted || actual.review !== expected.review) {
    throw new Error(`Catalog summary does not match candidates endpoint: summary=${JSON.stringify(actual)} candidates=${JSON.stringify(expected)}.`);
  }
}

async function waitForServer() {
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${baseURL}/demo/icp_radars.json`);
      if (response.ok) {
        return;
      }
    } catch {
      // Vite is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for ${baseURL}.`);
}
