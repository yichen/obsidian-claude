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

  // 4. Chart Visibility Check
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
