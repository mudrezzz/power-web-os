import { chromium } from '@playwright/test';

const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_RADAR_UI_DOD_BASE_URL ?? 'http://127.0.0.1:5173';
const preferredRadarId = process.env.POWER_WEB_OS_RADAR_SPLIT_RADAR_ID ?? 'benchmark-sibur-holding-contour';
const initialRunId = process.env.POWER_WEB_OS_SIGNAL_INITIAL_RUN_ID ?? 'signal-run-010ef75d-c626-44e3-a025-56c95522c1a8';
const incrementalRunId = process.env.POWER_WEB_OS_SIGNAL_INCREMENTAL_RUN_ID ?? 'signal-run-df00b3b8-267c-4091-a4dd-8167434e2cf3';
const waitMs = 30000;

const fixture = await loadSplitFixture();
const browser = await chromium.launch();

try {
  for (const scenario of [
    { locale: 'en', viewport: { width: 1280, height: 720 } },
    { locale: 'ru', viewport: { width: 1366, height: 768 } },
  ]) {
    await verifyScenario(browser, fixture, scenario);
  }
  await verifyMissingRunIsExplicit(browser);
  console.log('Radar pipeline split UI DoD passed.');
  console.log(JSON.stringify({
    radar_id: fixture.radar.radar_id,
    candidate_run_id: fixture.signal.source_run_id,
    signal_run_id: fixture.signal.run_id,
    signal_history_count: fixture.signalHistory.length,
    candidate_count: fixture.signal.output.candidate_count,
    observation_count: fixture.signal.output.observation_count,
  }, null, 2));
} finally {
  await browser.close();
}

async function verifyScenario(browserInstance, expected, { locale, viewport }) {
  console.log(`Checking ${locale} at ${viewport.width}x${viewport.height}.`);
  const errors = [];
  const context = await browserInstance.newContext({ viewport });
  await context.addInitScript((language) => {
    window.localStorage.clear();
    window.localStorage.setItem('power-web-os-locale', language);
  }, locale);
  const page = await context.newPage();
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text());
  });
  page.on('pageerror', (error) => errors.push(error.message));
  try {
    await page.goto(`${baseURL}?signalRunId=${encodeURIComponent(expected.signal.run_id)}`, {
      waitUntil: 'domcontentloaded',
    });
    try {
      await page.getByText(expected.radar.name, { exact: true }).waitFor({ state: 'visible', timeout: waitMs });
    } catch (error) {
      console.error(`Visible page text for ${locale}:\n${(await page.locator('body').innerText()).slice(0, 4000)}`);
      console.error(`Browser errors for ${locale}:\n${errors.join('\n')}`);
      throw error;
    }
    await page.locator('#radar-run-selector').waitFor({ state: 'visible', timeout: waitMs });
    await page.locator('#signal-monitoring-run-selector').waitFor({ state: 'visible', timeout: waitMs });
    await assertSelectValue(page, '#radar-run-selector', expected.signal.source_run_id);
    await assertSelectValue(page, '#signal-monitoring-run-selector', expected.signal.run_id);
    await page.getByText(expected.signal.source_run_id, { exact: false }).first().waitFor({ state: 'visible' });
    await page.getByText(expected.signal.run_id, { exact: false }).first().waitFor({ state: 'visible' });
    console.log(`Loaded linked runs for ${locale}.`);

    const url = new URL(page.url());
    if (url.searchParams.get('runId') !== expected.signal.source_run_id) {
      throw new Error(`Candidate run URL is not synchronized: ${url}.`);
    }
    if (url.searchParams.get('signalRunId') !== expected.signal.run_id) {
      throw new Error(`Signal run URL is not synchronized: ${url}.`);
    }

    const expectedText = locale === 'ru'
      ? ['Кого мониторить', 'Что нового произошло', 'Бюджет поиска кандидатов', 'Вызовы провайдера']
      : ['Who to monitor', 'What changed', 'Candidate discovery budget', 'Provider calls'];
    for (const text of expectedText) {
      await page.getByText(text, { exact: true }).first().waitFor({ state: 'visible' });
    }
    await assertLayout(page, viewport);
    if (await page.getByText('Demo fallback', { exact: true }).count()) {
      throw new Error('API-backed split UI rendered demo fallback state.');
    }
    if (await page.getByText('Recorded report', { exact: true }).count()) {
      throw new Error('API-backed split UI rendered the static recorded report as persisted output.');
    }

    const reportButton = page.getByRole('button', {
      name: locale === 'ru' ? 'Открыть отчет' : 'Open report',
      exact: true,
    });
    await reportButton.click();
    await page.getByText(expected.report.artifact_version, { exact: true }).waitFor({ state: 'visible' });
    await page.getByText(expected.report.source_candidate_run_id, { exact: false }).last().waitFor({ state: 'visible' });
    await assertSignalSurface(page, expected.incrementalSurface);
    console.log(`Validated incremental surface for ${locale}.`);

    const initial = expected.signalHistory.find((run) => run.run_id === initialRunId && run.output);
    if (initial) {
      await page.locator('#signal-monitoring-run-selector').selectOption(initial.run_id);
      await assertSelectValue(page, '#signal-monitoring-run-selector', initial.run_id);
      await assertSelectValue(page, '#radar-run-selector', initial.source_run_id);
      await page.waitForFunction(({ candidateRunId, signalRunId }) => {
        const params = new URL(window.location.href).searchParams;
        return params.get('runId') === candidateRunId && params.get('signalRunId') === signalRunId;
      }, { candidateRunId: initial.source_run_id, signalRunId: initial.run_id }, { timeout: waitMs });
      await assertSignalSurface(page, expected.initialSurface);
      console.log(`Validated initial surface for ${locale}.`);
    }

    await page.getByTestId('radar-tab-shortlist').click();
    await page.getByTestId('candidate-monitoring-column').waitFor({ state: 'visible' });
    await assertCandidateOverlay(page, expected.initialSurface);
    console.log(`Validated candidate overlay for ${locale}.`);
    if (errors.length) {
      throw new Error(`Browser errors for ${locale} ${viewport.width}x${viewport.height}:\n${errors.join('\n')}`);
    }
  } finally {
    await context.close();
  }
}

async function verifyMissingRunIsExplicit(browserInstance) {
  const context = await browserInstance.newContext({ viewport: { width: 1280, height: 720 } });
  await context.addInitScript(() => {
    window.localStorage.clear();
    window.localStorage.setItem('power-web-os-locale', 'en');
  });
  const page = await context.newPage();
  try {
    await page.goto(`${baseURL}?signalRunId=signal-run-missing-split-contract`, { waitUntil: 'domcontentloaded' });
    await page.getByText(/Signal monitoring run not found|404/, { exact: false }).waitFor({ state: 'visible', timeout: waitMs });
  } finally {
    await context.close();
  }
}

async function loadSplitFixture() {
  const radar = await apiJson(`/api/radars/${encodeURIComponent(preferredRadarId)}`);
  const signalHistory = await apiJson(`/api/radars/${encodeURIComponent(radar.radar_id)}/signal-monitoring-runs?limit=20`);
  const completed = signalHistory.filter((run) => run.status === 'completed' && run.output);
  const signal = completed.find((run) => run.run_id === incrementalRunId);
  const initial = completed.find((run) => run.run_id === initialRunId);
  if (!signal || !initial) {
    throw new Error(`Radar ${radar.radar_id} does not contain both required persisted signal runs.`);
  }
  const candidateRuns = await apiJson(`/api/radars/${encodeURIComponent(radar.radar_id)}/runs?limit=100`);
  const candidate = candidateRuns.find((run) => run.run_id === signal.source_run_id && run.status === 'completed' && run.output);
  if (!candidate) throw new Error(`Source candidate run ${signal.source_run_id} is missing or incomplete.`);
  const report = await apiJson(`/api/signal-monitoring-runs/${encodeURIComponent(signal.run_id)}/report`);
  if (report.source_candidate_run_id !== candidate.run_id || report.pipeline_id !== 'signal_monitoring') {
    throw new Error(`Signal run ${signal.run_id} has inconsistent source lineage.`);
  }
  const incrementalSurface = await apiJson(`/api/signal-monitoring-runs/${encodeURIComponent(signal.run_id)}/candidate-surface`);
  const initialSurface = await apiJson(`/api/signal-monitoring-runs/${encodeURIComponent(initial.run_id)}/candidate-surface`);
  return { radar, candidate, signal, signalHistory: completed, report, incrementalSurface, initialSurface };
}

async function assertSignalSurface(page, surface) {
  await page.waitForFunction((expectedRunId) => {
    return document.body.textContent?.includes(expectedRunId);
  }, surface.selected_run_id, { timeout: waitMs });
  const groups = page.locator('.radar-signal-candidate-group');
  const outcomes = page.locator('.radar-signal-outcome-row');
  if (await groups.count() !== surface.summary.monitored_candidate_count) {
    throw new Error(`Expected ${surface.summary.monitored_candidate_count} candidate groups, got ${await groups.count()}.`);
  }
  if (await outcomes.count() !== surface.summary.pair_count) {
    throw new Error(`Expected ${surface.summary.pair_count} pair outcomes, got ${await outcomes.count()}.`);
  }
  const summaryText = await page.getByTestId('signal-check-summary').textContent();
  for (const value of [surface.summary.monitored_candidate_count, surface.summary.criterion_count, surface.summary.pair_count]) {
    if (!summaryText?.includes(String(value))) throw new Error(`Signal check summary omits ${value}: ${summaryText}.`);
  }
  const metrics = await page.locator('.radar-signal-surface-summary > div').evaluateAll((items) => (
    items.map((item) => Number(item.getAttribute('data-value')))
  ));
  const expectedCounts = [
    surface.summary.new_confirmed_count,
    surface.summary.cumulative_confirmed_count - surface.summary.new_confirmed_count,
    surface.summary.current_review_count,
    surface.summary.current_searched_negative_count,
  ];
  expectedCounts.forEach((count, index) => {
    if (metrics[index] !== count) throw new Error(`Signal metric ${index} is ${metrics[index]}, expected ${count}.`);
  });
  const requiredEvidence = surface.candidates
    .flatMap((candidate) => candidate.outcomes)
    .filter((outcome) => ['found_fresh', 'found_relevant_date_unknown'].includes(outcome.cumulative.presentation_status));
  if (requiredEvidence.some((outcome) => !outcome.cumulative.evidence.some((item) => item.resolved))) {
    throw new Error('Backend surface contains retained/confirmed outcome without resolved evidence.');
  }
  if (await page.locator('.radar-signal-evidence-list a').count() === 0) {
    throw new Error('Signal report rendered no source links.');
  }
}

async function assertCandidateOverlay(page, surface) {
  const monitored = surface.candidates.filter((candidate) => candidate.monitored);
  for (const candidate of monitored) {
    const row = page.locator('.icp-candidate-row').filter({ hasText: candidate.candidate_name }).first();
    await row.waitFor({ state: 'visible', timeout: waitMs });
    const status = await row.locator('[data-monitoring-status]').getAttribute('data-monitoring-status');
    if (status !== candidate.monitoring_status) {
      throw new Error(`Candidate ${candidate.candidate_id} monitoring overlay is ${status}, expected ${candidate.monitoring_status}.`);
    }
  }
  if (surface.summary.not_monitored_candidate_count > 0 && await page.locator('[data-monitoring-status="not_monitored"]').count() === 0) {
    throw new Error('Candidates outside monitoring scope are not marked explicitly.');
  }
}

async function apiJson(path) {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`${path} failed: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

async function assertSelectValue(page, selector, expected) {
  await page.waitForFunction(({ css, value }) => {
    const element = document.querySelector(css);
    return element instanceof HTMLSelectElement && element.value === value;
  }, { css: selector, value: expected }, { timeout: waitMs });
}

async function assertLayout(page, viewport) {
  const layout = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.radar-pipeline-card')).map((element) => {
      const rect = element.getBoundingClientRect();
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom };
    });
    return {
      bodyWidth: document.body.scrollWidth,
      viewportWidth: document.documentElement.clientWidth,
      cards,
    };
  });
  if (layout.bodyWidth > layout.viewportWidth + 1) {
    throw new Error(`Body overflows horizontally at ${viewport.width}x${viewport.height}: ${layout.bodyWidth}px.`);
  }
  if (layout.cards.length !== 2) {
    throw new Error(`Expected two pipeline panels, got ${layout.cards.length}.`);
  }
  const [candidate, signal] = layout.cards;
  const overlaps = candidate.left < signal.right
    && candidate.right > signal.left
    && candidate.top < signal.bottom
    && candidate.bottom > signal.top;
  if (overlaps) {
    throw new Error(`Pipeline panels overlap at ${viewport.width}x${viewport.height}.`);
  }
}
