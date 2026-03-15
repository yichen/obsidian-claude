import { test, expect } from '@playwright/test';

/**
 * UI AUDIT TEST
 * This test programmatically measures the UI quality to catch "terrible" results 
 * without human intervention.
 */

test('Audit: Dashboard Layout and Spacing', async ({ page }) => {
  // 1. Navigate to the local app (assuming dev server is on 5173)
  try {
    await page.goto('http://localhost:5173', { timeout: 60000 });
    // Check if the body exists first
    await page.waitForSelector('body', { timeout: 10000 });
    
    // Take a screenshot to "see" the state
    await page.screenshot({ path: 'tests/audit-baseline.png' });
    console.log('Baseline screenshot saved to tests/audit-baseline.png');

    await page.waitForSelector('.dashboard-container', { timeout: 20000 });
  } catch (e) {
    await page.screenshot({ path: 'tests/audit-error.png' });
    const content = await page.content();
    console.log('Page Content Sample:', content.substring(0, 500));
    throw e;
  }

  // 2. Measure White Space Ratio
  // We check if the main containers are actually taking up space
  const mainContent = await page.locator('.main-content');
  const box = await mainContent.boundingBox();
  expect(box?.width).toBeGreaterThan(500); // Layout hasn't collapsed
  expect(box?.height).toBeGreaterThan(500);

  // 3. Font Consistency Check
  const fontSizes = await page.evaluate(() => {
    const elements = document.querySelectorAll('h1, h2, p, .message-bubble');
    const sizes = Array.from(elements).map(el => window.getComputedStyle(el).fontSize);
    return [...new Set(sizes)]; // Unique font sizes
  });
  console.log('Detected Font Sizes:', fontSizes);
  
  // We expect a controlled number of font sizes (e.g., small, base, large, xl)
  // If we have 15 different font sizes, it's inconsistent.
  expect(fontSizes.length).toBeLessThan(10);

  // 3b. Drag bar check
  await page.waitForSelector('.window-drag-bar', { timeout: 10000 });
  const dragStyles = await page.evaluate(() => {
    const el = document.querySelector('.window-drag-bar')!;
    const cs = window.getComputedStyle(el);
    return {
      position: cs.position,
      pointerEvents: cs.pointerEvents,
      appRegion: cs.getPropertyValue('-webkit-app-region'),
      height: cs.height,
    };
  });
  expect(dragStyles.position).toBe('fixed');
  expect(dragStyles.pointerEvents).toBe('none');
  expect(dragStyles.appRegion).toBe('drag');
  expect(parseInt(dragStyles.height)).toBeGreaterThanOrEqual(40);

  // 4a. Deep Dive sends exactly one user message
  await page.reload();
  await page.waitForSelector('.dashboard-container', { timeout: 20000 });
  const deepDiveBefore = await page.locator('.message-row.user').count();
  await page.locator('.deep-dive-btn').first().click();
  await page.waitForSelector('.message-row.user', { timeout: 10000 });
  await page.waitForTimeout(500);
  const deepDiveAfter = await page.locator('.message-row.user').count();
  expect(deepDiveAfter - deepDiveBefore).toBe(1);

  // 4b. Dashboard container fills available width without large right gap
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload();
  await page.waitForSelector('.dashboard-container', { timeout: 20000 });
  const containerBox = await page.locator('.dashboard-container').boundingBox();
  const mainBox = await page.locator('.main-content').boundingBox();
  expect(containerBox).not.toBeNull();
  expect(mainBox).not.toBeNull();
  expect(containerBox!.width / mainBox!.width).toBeGreaterThan(0.9);

  // 5. Chart Visibility Check
  await page.click('text=Chat');

  await page.fill('textarea', 'Show me a spending dashboard');
  await page.click('.send-btn');
  
  // Wait for a chart to potentially appear (standard chart tool)
  const chart = page.locator('.chart-image');
  try {
    await chart.waitFor({ state: 'visible', timeout: 30000 });
    const chartBox = await chart.boundingBox();
    
    // Check if chart is cut off (smaller than container or 0 height)
    expect(chartBox?.height).toBeGreaterThan(100);
    
    // Check for horizontal overflow (terrible UX)
    const chatArea = await page.locator('.messages-area').boundingBox();
    expect(chartBox?.width).toBeLessThanOrEqual(chatArea?.width || 0);
  } catch (e) {
    console.log('No chart generated in this audit round.');
  }
});

test('Gutter: all pages share the same 32px left/right gutter', async ({ page }) => {
  await page.goto('http://localhost:5173', { timeout: 60000 });
  await page.waitForSelector('.dashboard-container', { timeout: 20000 });

  // Dashboard — header provides 32px padding
  const dashGutter = await page.evaluate(() => {
    const el = document.querySelector('.dashboard-container .page-header')!;
    const cs = window.getComputedStyle(el);
    return { left: parseInt(cs.paddingLeft), right: parseInt(cs.paddingRight) };
  });
  expect(dashGutter.left).toBe(32);
  expect(dashGutter.right).toBe(32);

  // Transactions
  await page.click('text=Transactions');
  await page.waitForSelector('.page-header.txn-top-bar', { timeout: 10000 });
  const txnGutter = await page.evaluate(() => {
    const el = document.querySelector('.page-header.txn-top-bar')!;
    const cs = window.getComputedStyle(el);
    return { left: parseInt(cs.paddingLeft), right: parseInt(cs.paddingRight) };
  });
  expect(txnGutter.left).toBe(32);
  expect(txnGutter.right).toBe(32);

  // Chat
  await page.click('text=Chat');
  await page.waitForSelector('.messages-area', { timeout: 10000 });
  const chatGutter = await page.evaluate(() => {
    const el = document.querySelector('.messages-area')!;
    const cs = window.getComputedStyle(el);
    return { left: parseInt(cs.paddingLeft), right: parseInt(cs.paddingRight) };
  });
  expect(chatGutter.left).toBe(32);
  expect(chatGutter.right).toBe(32);
});

test('Dashboard overview charts: all four charts render images', async ({ page }) => {
  await page.goto('http://localhost:5173', { timeout: 60000 });
  await page.waitForSelector('.dashboard-container', { timeout: 20000 });

  // Wait for charts to load (they start as "Loading..." then become <img> or "No data available")
  // Give charts up to 30s to render since they involve Python execution
  const chartCards = page.locator('.overview-chart-card');
  await expect(chartCards).toHaveCount(2); // Income card + Spending card

  // Income bar chart
  const incomeImg = chartCards.nth(0).locator('img[alt="Income"]');
  await expect(incomeImg).toBeVisible({ timeout: 30000 });

  // Income pie chart (By Source)
  const incomePieImg = chartCards.nth(0).locator('img[alt="Income by Source"]');
  await expect(incomePieImg).toBeVisible({ timeout: 30000 });

  // Spending bar chart
  const spendingImg = chartCards.nth(1).locator('img[alt="Spending"]');
  await expect(spendingImg).toBeVisible({ timeout: 30000 });

  // Spending pie chart (By Category)
  const spendingPieImg = chartCards.nth(1).locator('img[alt="Spending by Category"]');
  await expect(spendingPieImg).toBeVisible({ timeout: 30000 });

  // Verify no "No data available" messages are shown
  const noData = page.locator('.overview-chart-loading', { hasText: 'No data available' });
  await expect(noData).toHaveCount(0);
});

test('All page headers use unified .page-header with consistent padding and divider', async ({ page }) => {
  await page.goto('http://localhost:5173', { timeout: 60000 });

  // Dashboard
  await page.waitForSelector('.dashboard-container .page-header');
  const dashHeader = await page.evaluate(() => {
    const el = document.querySelector('.dashboard-container .page-header')!;
    const cs = getComputedStyle(el);
    return { paddingTop: cs.paddingTop, borderBottom: cs.borderBottomWidth, borderStyle: cs.borderBottomStyle };
  });
  expect(dashHeader.paddingTop).toBe('32px');
  expect(dashHeader.borderBottom).toBe('1px');
  expect(dashHeader.borderStyle).toBe('solid');

  // Transactions
  await page.click('text=Transactions');
  await page.waitForSelector('.page-header.txn-top-bar');
  const txnHeader = await page.evaluate(() => {
    const el = document.querySelector('.page-header.txn-top-bar')!;
    const cs = getComputedStyle(el);
    return { paddingTop: cs.paddingTop, borderBottom: cs.borderBottomWidth, borderStyle: cs.borderBottomStyle };
  });
  expect(txnHeader.paddingTop).toBe('32px');
  expect(txnHeader.borderBottom).toBe('1px');
  expect(txnHeader.borderStyle).toBe('solid');

  // Chat
  await page.click('text=Chat');
  await page.waitForSelector('.page-header.chat-header');
  const chatHeader = await page.evaluate(() => {
    const el = document.querySelector('.page-header.chat-header')!;
    const cs = getComputedStyle(el);
    return { paddingTop: cs.paddingTop, borderBottom: cs.borderBottomWidth, borderStyle: cs.borderBottomStyle };
  });
  expect(chatHeader.paddingTop).toBe('32px');
  expect(chatHeader.borderBottom).toBe('1px');
  expect(chatHeader.borderStyle).toBe('solid');
});

test('All page titles use consistent 24px font size', async ({ page }) => {
  await page.goto('http://localhost:5173', { timeout: 60000 });
  // Dashboard
  await page.waitForSelector('.page-header h1');
  expect(await page.$eval('.page-header h1', el => getComputedStyle(el).fontSize)).toBe('24px');
  // Transactions
  await page.click('text=Transactions');
  await page.waitForSelector('.page-header.txn-top-bar h1');
  expect(await page.$eval('.page-header.txn-top-bar h1', el => getComputedStyle(el).fontSize)).toBe('24px');
  // AI Chat
  await page.click('text=Chat');
  await page.waitForSelector('.page-header.chat-header h1');
  expect(await page.$eval('.page-header.chat-header h1', el => getComputedStyle(el).fontSize)).toBe('24px');
});

test('All page header titles have the same horizontal position', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:5173', { timeout: 60000 });

  // Dashboard
  await page.waitForSelector('.page-header h1');
  const dashLeft = await page.$eval('.page-header h1', el => el.getBoundingClientRect().left);

  // Transactions
  await page.click('text=Transactions');
  await page.waitForSelector('.page-header.txn-top-bar h1');
  const txnLeft = await page.$eval('.page-header.txn-top-bar h1', el => el.getBoundingClientRect().left);

  // Chat
  await page.click('text=Chat');
  await page.waitForSelector('.page-header.chat-header h1');
  const chatLeft = await page.$eval('.page-header.chat-header h1', el => el.getBoundingClientRect().left);

  // All three should be at the same horizontal position (sidebar width + header padding)
  expect(txnLeft).toBe(dashLeft);
  expect(chatLeft).toBe(dashLeft);
});
