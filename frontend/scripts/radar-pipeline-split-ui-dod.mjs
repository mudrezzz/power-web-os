import { chromium } from '@playwright/test';

const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_RADAR_UI_DOD_BASE_URL ?? 'http://127.0.0.1:5173';
const preferredRadarId = process.env.POWER_WEB_OS_RADAR_SPLIT_RADAR_ID ?? 'benchmark-sibur-holding-contour';
const waitMs = 90000;

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
    await page.getByText(expected.radar.name, { exact: true }).waitFor({ state: 'visible', timeout: waitMs });
    await page.locator('#radar-run-selector').waitFor({ state: 'visible', timeout: waitMs });
    await page.locator('#signal-monitoring-run-selector').waitFor({ state: 'visible', timeout: waitMs });
    await assertSelectValue(page, '#radar-run-selector', expected.signal.source_run_id);
    await assertSelectValue(page, '#signal-monitoring-run-selector', expected.signal.run_id);
    await page.getByText(expected.signal.source_run_id, { exact: false }).first().waitFor({ state: 'visible' });
    await page.getByText(expected.signal.run_id, { exact: false }).first().waitFor({ state: 'visible' });

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

    const second = expected.signalHistory.find((run) => run.run_id !== expected.signal.run_id && run.output);
    if (second) {
      await page.locator('#signal-monitoring-run-selector').selectOption(second.run_id);
      await assertSelectValue(page, '#signal-monitoring-run-selector', second.run_id);
      await assertSelectValue(page, '#radar-run-selector', second.source_run_id);
      await page.waitForFunction(({ candidateRunId, signalRunId }) => {
        const params = new URL(window.location.href).searchParams;
        return params.get('runId') === candidateRunId && params.get('signalRunId') === signalRunId;
      }, { candidateRunId: second.source_run_id, signalRunId: second.run_id }, { timeout: waitMs });
    }
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
  const radars = await apiJson('/api/radars');
  const ordered = [...radars].sort((left, right) => (
    left.radar_id === preferredRadarId ? -1 : right.radar_id === preferredRadarId ? 1 : 0
  ));
  for (const radar of ordered) {
    const signalHistory = await apiJson(`/api/radars/${encodeURIComponent(radar.radar_id)}/signal-monitoring-runs?limit=20`);
    const completed = signalHistory.filter((run) => run.status === 'completed' && run.output);
    if (completed.length < 2) continue;
    const signal = completed[0];
    const candidateRuns = await apiJson(`/api/radars/${encodeURIComponent(radar.radar_id)}/runs?limit=100`);
    const candidate = candidateRuns.find((run) => run.run_id === signal.source_run_id && run.status === 'completed' && run.output);
    if (!candidate) continue;
    const report = await apiJson(`/api/signal-monitoring-runs/${encodeURIComponent(signal.run_id)}/report`);
    if (report.source_candidate_run_id !== candidate.run_id || report.pipeline_id !== 'signal_monitoring') continue;
    return { radar, candidate, signal, signalHistory: completed, report };
  }
  throw new Error('Backend has no radar with one completed candidate run and at least two linked completed signal runs.');
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
