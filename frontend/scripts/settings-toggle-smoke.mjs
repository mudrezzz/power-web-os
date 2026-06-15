import { chromium } from '@playwright/test';
import path from 'node:path';
import { createServer } from 'vite';

const frontendRoot = path.resolve('.');
const port = Number(process.env.POWER_WEB_OS_TOGGLE_SMOKE_PORT ?? 4188);
const baseURL = `http://127.0.0.1:${port}`;
const errors = [];

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
  browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('pageerror', (error) => errors.push(error.stack || error.message));
  page.on('console', (message) => {
    if (message.type() === 'error') {
      errors.push(message.text());
    }
  });
  await page.goto(baseURL, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => {
    window.localStorage.setItem('power-web-os-locale', 'ru');
    window.localStorage.removeItem('power-web-os-icp-radar-config-overrides');
  });
  await page.reload({ waitUntil: 'domcontentloaded' });

  await openFirstRadarSettings(page);
  await assertHealthy(page, 'settings open');

  let clicked = 0;

  clicked += await toggleGlobalSearchAndPersist(page);
  await page.reload({ waitUntil: 'domcontentloaded' });
  await openFirstRadarSettings(page);
  await page.locator('.icp-settings-section').first().locator('.icp-editor-actions button').last().click();
  await page.locator('.icp-settings-section').first().locator('.toggle-field').last().click();
  clicked += 1;
  await assertHealthy(page, 'persisted global search switch after reload');
  await page.locator('.icp-settings-section').first().locator('.icp-editor-actions button').nth(2).click();

  await page.locator('.icp-radar-header .icp-editor-actions button').first().click();
  clicked += await clickAllTogglesIn(page.locator('.icp-radar-header'), page, 'selected radar header');
  await page.locator('.icp-radar-header .icp-editor-actions button').nth(1).click();
  await assertHealthy(page, 'selected radar header discard');

  const blockCount = await page.locator('.icp-settings-section').count();
  for (let blockIndex = 0; blockIndex < blockCount; blockIndex += 1) {
    const section = page.locator('.icp-settings-section').nth(blockIndex);
    const editButtons = section.locator('.icp-editor-actions button');
    if ((await editButtons.count()) < 1) {
      continue;
    }
    await editButtons.last().click();
    await assertHealthy(page, `settings block ${blockIndex + 1} edit open`);
    clicked += await clickAllTogglesIn(page.locator('.icp-settings-section').nth(blockIndex), page, `settings block ${blockIndex + 1}`);

    const actionButtons = page.locator('.icp-settings-section').nth(blockIndex).locator('.icp-editor-actions button');
    if ((await actionButtons.count()) >= 2) {
      await actionButtons.nth(1).click();
      await assertHealthy(page, `settings block ${blockIndex + 1} discard`);
    }
  }

  clicked += await clickGlobalSearchSwitchWithLegacyOverride(page);

  if (clicked < 90) {
    throw new Error(`Settings toggle smoke clicked only ${clicked} switches; expected at least 90.`);
  }

  console.log(`Settings toggle smoke passed: ${clicked} switch clicks`);
} finally {
  if (browser) {
    await browser.close();
  }
  await server.close();
}

async function openFirstRadarSettings(page) {
  await page.locator('.icp-radar-list-row').first().waitFor({ state: 'visible' });
  await page.locator('.icp-radar-list-row').first().click();
  await page.locator('.icp-radar-tabs button').nth(1).waitFor({ state: 'visible' });
  await page.locator('.icp-radar-tabs button').nth(1).click();
  await page.locator('.icp-settings-section').first().waitFor({ state: 'visible' });
}

async function toggleGlobalSearchAndPersist(page) {
  const section = page.locator('.icp-settings-section').first();
  await section.locator('.icp-editor-actions button').last().click();
  await section.locator('.toggle-field').last().scrollIntoViewIfNeeded();
  await section.locator('.toggle-field').last().click();
  await assertHealthy(page, 'global search switch before save');
  const saveButton = page.locator('.icp-settings-section').first().locator('.icp-editor-actions button').nth(1);
  if (await saveButton.isDisabled()) {
    throw new Error('Global search save button is disabled after switching additional sources.');
  }
  await saveButton.click();
  await assertHealthy(page, 'global search switch saved');
  const stored = await page.evaluate(() => window.localStorage.getItem('power-web-os-icp-radar-config-overrides'));
  if (!stored || stored.length < 100) {
    throw new Error('Global search switch save did not persist a radar override.');
  }
  return 1;
}

async function clickGlobalSearchSwitchWithLegacyOverride(page) {
  await page.evaluate(async () => {
    const catalog = await fetch('/demo/icp_radars.json').then((response) => response.json());
    const radar = catalog.radars[0];
    const legacyRadar = {
      ...radar,
      definition: {
        ...radar.definition,
        global_search_policy: {
          allow_system_sources: true,
        },
        intent_signals: radar.definition.intent_signals.map((signal) => ({
          ...signal,
          source_policy: {
            use_global_search_policy: true,
            allow_additional_sources: true,
            source_logic: 'OR',
          },
        })),
      },
    };
    window.localStorage.setItem('power-web-os-icp-radar-config-overrides', JSON.stringify({
      [radar.radar_id]: {
        override_type: 'edited',
        radar: legacyRadar,
        saved_at: new Date().toISOString(),
      },
    }));
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await openFirstRadarSettings(page);
  await assertHealthy(page, 'legacy override settings open');
  const section = page.locator('.icp-settings-section').first();
  await section.locator('.icp-editor-actions button').last().click();
  await section.locator('.toggle-field').last().click();
  await assertHealthy(page, 'legacy override global search switch');
  return 1;
}

async function clickAllTogglesIn(scope, page, label) {
  let count = await scope.locator('.toggle-field').count();
  let clicks = 0;
  for (let index = 0; index < count; index += 1) {
    for (let pass = 0; pass < 2; pass += 1) {
      const toggles = scope.locator('.toggle-field');
      count = await toggles.count();
      if (index >= count) {
        break;
      }
      const toggle = toggles.nth(index);
      const text = (await toggle.innerText().catch(() => '')).replace(/\s+/g, ' ').trim();
      await toggle.scrollIntoViewIfNeeded();
      await toggle.click();
      clicks += 1;
      await assertHealthy(page, `${label} switch ${index + 1} "${text}" pass ${pass + 1}`);
    }
  }
  return clicks;
}

async function assertHealthy(page, label) {
  await page.waitForTimeout(50);
  if (errors.length > 0) {
    throw new Error(`${label}: page errors: ${errors.join('; ')}`);
  }
  const bodyText = await page.locator('body').innerText().catch(() => '');
  const appShellCount = await page.locator('.app-shell').count().catch(() => 0);
  const settingsSectionCount = await page.locator('.icp-settings-section').count().catch(() => 0);
  const viewportState = await page.evaluate(() => {
    const shell = document.querySelector('.app-shell')?.getBoundingClientRect();
    const sidebar = document.querySelector('.sidebar')?.getBoundingClientRect();
    return {
      shellTop: shell?.top ?? null,
      shellBottom: shell?.bottom ?? null,
      sidebarTop: sidebar?.top ?? null,
      scrollX: window.scrollX,
      scrollY: window.scrollY,
    };
  });
  if (appShellCount < 1 || bodyText.trim().length < 80 || settingsSectionCount < 1) {
    throw new Error(
      `${label}: settings UI became unhealthy: appShell=${appShellCount}, settingsSections=${settingsSectionCount}, bodyLength=${bodyText.trim().length}`,
    );
  }
  if (
    viewportState.shellTop !== 0
    || viewportState.sidebarTop !== 0
    || viewportState.shellBottom !== page.viewportSize()?.height
    || viewportState.scrollX !== 0
    || viewportState.scrollY !== 0
  ) {
    throw new Error(`${label}: SPA shell left viewport: ${JSON.stringify(viewportState)}`);
  }
}
