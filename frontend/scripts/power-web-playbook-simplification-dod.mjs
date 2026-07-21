import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';

const apiBaseUrl = process.env.POWER_WEB_OS_API_BASE_URL ?? 'http://127.0.0.1:8001';
const baseURL = process.env.POWER_WEB_OS_UI_DOD_BASE_URL ?? 'http://127.0.0.1:5173';
const productId = 'product-smartdiagnostics';
const browser = await chromium.launch();

try {
  await mkdir('test-results', { recursive: true });
  await waitFor(`${apiBaseUrl}/api/health`);
  await waitFor(baseURL);
  const products = await json(`${apiBaseUrl}/api/products`);
  const product = products.find((item) => item.product_id === productId);
  if (!product) throw new Error('SmartDiagnostics seed is missing.');
  const draft = await json(`${apiBaseUrl}/api/products/${productId}/draft`);
  if (draft.buying_roles.length < 8) throw new Error('SmartDiagnostics requires at least eight semantic roles.');

  let versions = await json(`${apiBaseUrl}/api/products/${productId}/versions`);
  if (versions.find((item) => item.is_active)?.access_playbook_version_id) {
    const response = await fetch(`${apiBaseUrl}/api/products/${productId}/publish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requester: 'ui-dod-upgrade', activate: true }),
    });
    if (!response.ok) throw new Error(`Compatibility publication returned ${response.status}.`);
    versions = await json(`${apiBaseUrl}/api/products/${productId}/versions`);
  }
  const active = versions.find((item) => item.is_active);
  if (!active || active.access_playbook_version_id !== null || active.access_playbook !== null) {
    throw new Error('Active configuration still depends on AccessPlaybook.');
  }

  const results = [];
  let roundTripVerified = false;
  for (const locale of ['ru', 'en']) {
    for (const viewport of [{ width: 1280, height: 720 }, { width: 1366, height: 768 }]) {
      const context = await browser.newContext({ viewport });
      await context.addInitScript((language) => window.localStorage.setItem('power-web-os-locale', language), locale);
      const page = await context.newPage();
      const errors = [];
      page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
      page.on('pageerror', (error) => errors.push(error.message));
      await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
      await page.locator('.nav-item').nth(5).click();
      await page.getByTestId('product-catalog').waitFor({ state: 'visible' });
      if (await page.getByTestId('sales-playbook-detail').count()) throw new Error('Catalog eagerly rendered product detail.');
      await page.getByTestId('product-smartdiagnostics').click();
      await page.getByTestId('sales-playbook-detail').waitFor({ state: 'visible' });
      if (!roundTripVerified) {
        const originalDescription = draft.product.short_description.replace(/(?: \[ui-round-trip[^\]]*\])+$/, '');
        const changedDescription = `${originalDescription} [ui-round-trip-${Date.now()}]`;
        await page.getByTestId('product-short-description').fill(changedDescription);
        await saveDraftThroughUi(page, changedDescription);
        await page.reload({ waitUntil: 'domcontentloaded' });
        await page.locator('.nav-item').nth(5).click();
        await page.getByTestId('sales-playbook-detail').waitFor({ state: 'visible' });
        if (await page.getByTestId('product-short-description').inputValue() !== changedDescription) throw new Error('Saved draft did not survive UI reload.');
        await page.getByTestId('product-short-description').fill(originalDescription);
        await saveDraftThroughUi(page, originalDescription);
        roundTripVerified = true;
      }
      await page.screenshot({ path: `test-results/playbook-workspace-${locale}-${viewport.width}x${viewport.height}.png` });
      await page.locator('.sales-playbook-detail > .workspace-tabs [role="tab"]').nth(1).click();
      await page.locator('.roles-table button.sales-table-row').first().click();
      const geometry = await page.evaluate(() => {
        const workspace = document.querySelector('.workspace-body')?.getBoundingClientRect();
        const screen = document.querySelector('.sales-playbook-screen')?.getBoundingClientRect();
        const detail = document.querySelector('.sales-playbook-detail')?.getBoundingClientRect();
        const backButton = document.querySelector('.sales-playbook-identity > button')?.getBoundingClientRect();
        const table = document.querySelector('[data-testid="roles-table"]')?.getBoundingClientRect();
        const editor = document.querySelector('[data-testid="role-inline-editor"]')?.getBoundingClientRect();
        const advanced = document.querySelector('[data-testid="role-advanced"]');
        return {
          screenRatio: workspace && screen ? screen.width / workspace.width : 0,
          detailRatio: screen && detail ? detail.width / screen.width : 0,
          topGutter: screen && detail ? detail.top - screen.top : 0,
          leftGutter: screen && detail ? detail.left - screen.left : 0,
          rightGutter: screen && detail ? screen.right - detail.right : 0,
          backButtonHeight: backButton?.height ?? 999,
          inlineWidthDelta: table && editor ? Math.abs(table.width - editor.width) : 999,
          bodyOverflow: document.documentElement.scrollHeight > window.innerHeight + 2,
          horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
          advancedOpen: advanced instanceof HTMLDetailsElement ? advanced.open : null,
        };
      });
      const basicFieldCount = await page.locator('[data-basic-role-field="true"]').count();
      const tabCount = await page.locator('.sales-playbook-detail > .workspace-tabs [role="tab"]').count();
      if (geometry.screenRatio < 0.99) throw new Error(`Playbook uses only ${geometry.screenRatio} of workspace width.`);
      if (geometry.detailRatio < 0.95) throw new Error(`Detail uses only ${geometry.detailRatio} of workspace width.`);
      if (geometry.topGutter < 20 || geometry.leftGutter < 20 || geometry.rightGutter < 20) {
        throw new Error(`Playbook workspace gutters are too small: ${JSON.stringify(geometry)}.`);
      }
      if (Math.abs(geometry.leftGutter - geometry.rightGutter) > 2) {
        throw new Error(`Playbook side gutters are not symmetric: ${JSON.stringify(geometry)}.`);
      }
      if (geometry.backButtonHeight > 44) throw new Error(`Back command wrapped to ${geometry.backButtonHeight}px.`);
      if (geometry.inlineWidthDelta > 2) throw new Error(`Inline editor width delta is ${geometry.inlineWidthDelta}px.`);
      if (geometry.bodyOverflow || geometry.horizontalOverflow) throw new Error(`Viewport overflow: ${JSON.stringify(geometry)}.`);
      if (geometry.advancedOpen !== false) throw new Error('Advanced role guidance is not collapsed by default.');
      if (basicFieldCount !== 4) throw new Error(`Expected four basic role fields, got ${basicFieldCount}.`);
      if (tabCount !== 3) throw new Error(`Expected three Playbook tabs, got ${tabCount}.`);
      if (await page.locator('.product-rail, .editor-inspector').count()) throw new Error('Legacy side columns remain visible.');
      await page.goBack();
      await page.getByTestId('product-catalog').waitFor({ state: 'visible' });
      if (errors.length) throw new Error(errors.join('\n'));
      results.push({ locale, viewport, ...geometry, basic_field_count: basicFieldCount, tab_count: tabCount });
      await context.close();
    }
  }

  const evidence = {
    validation_status: 'PASS',
    product_id: productId,
    active_version_id: active.version_id,
    semantic_role_count: draft.buying_roles.length,
    access_playbook_version_id: active.access_playbook_version_id,
    ui_api_db_reload_round_trip: roundTripVerified,
    results,
  };
  await writeFile('test-results/power-web-playbook-simplification.json', `${JSON.stringify(evidence, null, 2)}\n`);
  console.log('Power Web Playbook simplification DoD passed.');
  console.log(JSON.stringify(evidence, null, 2));
} finally {
  await browser.close();
}

async function json(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.json();
}

async function waitFor(url) {
  const deadline = Date.now() + 90_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // Docker services may still be starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }
  throw new Error(`Service was not ready: ${url}`);
}

async function saveDraftThroughUi(page, expectedDescription) {
  const button = page.getByTestId('save-draft-header');
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline && !(await button.isEnabled())) {
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  if (!(await button.isEnabled())) throw new Error('Save draft button did not become enabled.');
  await button.click();
  while (Date.now() < deadline) {
    const stored = await json(`${apiBaseUrl}/api/products/${productId}/draft`);
    if (stored.product.short_description === expectedDescription) return;
    await new Promise((resolve) => setTimeout(resolve, 150));
  }
  throw new Error(`Draft did not persist expected description: ${expectedDescription}`);
}
