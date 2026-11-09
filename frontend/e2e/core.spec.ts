import { test, expect, Page, APIRequestContext } from '@playwright/test';
import fs from 'node:fs/promises';

async function login(page: Page, email: string, password: string) {
  await page.goto('/login');
  await page.getByLabel('Staff Email').fill(email);
  await page.getByLabel('Password', { exact: false }).fill(password);
  await page.getByRole('button', { name: 'Sign In to Workshop Ledger' }).click();
  await expect(page).not.toHaveURL(/login/);
}

async function apiLogin(request: APIRequestContext, email: string, password: string) {
  const response = await request.post('/api/auth/login', { data: { email, password } });
  expect(response.ok()).toBeTruthy();
  return { Authorization: `Bearer ${(await response.json()).access_token}` };
}

test('clerk verifies a real OCR proposal and mismatch blocks saving', async ({ page }, info) => {
  await login(page, 'clerk@karigarflow.com', 'Clerk@123');
  await page.getByRole('link', { name: 'New slip', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.locator('select').nth(1).selectOption({ label: 'KG-CBE-001 - Anand Swamy' });
  await page.getByLabel('Job number').fill(`PW-OCR-${Date.now()}`);
  await page.getByLabel('Item Description', { exact: false }).fill('Browser verified scale issue');
  await dialog.locator('input[type=file]').setInputFiles('../database/seed/scale-demo.png');
  await expect(page.getByText('Weight: 120.000 g', { exact: true })).toBeVisible({ timeout: 30000 });
  await page.getByText('Proposed reading — confirm below').scrollIntoViewIfNeeded();
  await page.screenshot({ path: info.outputPath('scale-proposal.png') });
  await page.getByLabel('Gross Weight', { exact: false }).fill('119.000');
  await page.getByLabel('Human Confirmation of Scale Reading', { exact: false }).check();
  await page.getByRole('button', { name: 'Sign & Record Slip' }).click();
  await expect(page.getByText(/Typed values do not match the photo/)).toBeVisible();
  await page.screenshot({ path: info.outputPath('scale-review.png') });
  await page.getByLabel('Gross Weight', { exact: false }).fill('120.000');
  await page.getByLabel('Human Confirmation of Scale Reading', { exact: false }).check();
  await page.getByRole('button', { name: 'Sign & Record Slip' }).click();
  await expect(dialog).not.toBeVisible();
  await expect(page.getByText('Browser verified scale issue', { exact: true }).first()).toBeVisible();
  const ownerLink = page.getByRole('link', { name: 'Daily stock statement', exact: true });
  await expect(ownerLink).toHaveCount(0);
  await page.goto('/daily-stock');
  await expect(page.getByText('Access Restricted', { exact: true })).toBeVisible();
});

test('phone draft survives offline reload and is isolated from the next user', async ({ page, context }, info) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await login(page, 'clerk@karigarflow.com', 'Clerk@123');
  await page.goto('/slips');
  await page.getByRole('button', { name: 'Create New Slip' }).click();
  await page.getByRole('dialog').locator('select').nth(1).selectOption({ label: 'KG-CBE-001 - Anand Swamy' });
  await page.getByLabel('Job number').fill('PW-OFFLINE-DRAFT');
  await page.getByLabel('Item Description', { exact: false }).fill('Offline tablet draft');
  await page.getByLabel('Gross Weight', { exact: false }).fill('12.345');
  await page.waitForFunction(() => Object.keys(localStorage).some(key => key.startsWith('karigarflow-draft-v1-') && localStorage.getItem(key)?.includes('Offline tablet draft')));
  await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
  await context.setOffline(true);
  await page.reload();
  await expect(page.getByLabel('Job number')).toHaveValue('PW-OFFLINE-DRAFT');
  await expect(page.getByLabel('Gross Weight', { exact: false })).toHaveValue('12.345');
  await expect(page.getByText(/Offline — draft changes/)).toBeVisible();
  await expect(page.getByLabel('Human Confirmation of Scale Reading', { exact: false })).not.toBeChecked();
  await page.screenshot({ path: info.outputPath('phone-offline-draft.png'), fullPage: true });
  await context.setOffline(false);
  await page.reload();
  await expect(page.getByLabel('Job number')).toHaveValue('PW-OFFLINE-DRAFT');
  await page.getByRole('button', { name: 'Clear draft' }).click();
  await page.getByRole('button', { name: 'Cancel', exact: true }).click();
  await page.evaluate(() => { localStorage.removeItem('karigarflow_token'); localStorage.removeItem('karigarflow_user'); });
  await login(page, 'murugesan@karigarflow.com', 'Karigar@123');
  await expect(page.getByRole('heading', { name: 'என் தங்கக் கணக்கு' })).toBeVisible();
  await expect(page.getByText('3.893 g', { exact: true })).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: info.outputPath('phone-tamil-slips.png') });
});

test('finance reviews drift, changes an agreement and approves a linked write-off', async ({ page, request }, info) => {
  const clerk = await apiLogin(request, 'clerk@karigarflow.com', 'Clerk@123');
  const profiles = await (await request.get('/api/karigars', { headers: clerk })).json();
  const k = profiles.find((p: { karigar_code: string }) => p.karigar_code === 'KG-CBE-001');
  const job = `PW-LOSS-${Date.now()}`;
  const payload = { transaction_type: 'ISSUE', karigar_id: k.id, job_number: job, item_category: 'necklace', gross_weight: '20.000', purity_percent: '91.60', item_description: 'Browser loss review', scale_reading_confirmed: true };
  const issued = await request.post('/api/transactions', { headers: clerk, data: payload });
  expect(issued.status()).toBe(201);
  const receipt = await request.post('/api/transactions', { headers: clerk, data: { ...payload, transaction_type: 'RECEIPT_ORNAMENT', gross_weight: '10.000', actual_wastage_weight: '1.000' } });
  expect(receipt.status()).toBe(201);
  const slip = (await receipt.json()).slip_number;
  await login(page, 'finance@karigarflow.com', 'Finance@123');
  await page.goto('/karigars');
  await page.getByRole('button', { name: 'Edit agreements' }).first().click();
  await page.getByLabel('ring wastage percent').fill('1.55');
  await page.getByRole('button', { name: 'Save agreements' }).click();
  await expect(page.getByRole('dialog')).not.toBeVisible();
  await page.goto('/loss-alerts');
  await expect(page.getByText('Demo drift review · necklace', { exact: true })).toBeVisible();
  const card = page.locator('article').filter({ hasText: slip });
  await card.getByRole('button', { name: 'Review write-off' }).click();
  await page.getByLabel(/Investigation findings/).fill('Synthetic review: bench sweep complete and no recovery found.');
  await page.getByLabel(/I approve this exact excess/).check();
  await page.getByRole('button', { name: 'Approve write-off', exact: true }).click();
  await expect(page.getByText(/Write-off saved as/)).toBeVisible();
  await expect(page.getByRole('button', { name: /\d+ Alerts?/ })).toHaveCount(0);
  await page.getByRole('button', { name: 'Approved write-offs', exact: true }).click();
  await expect(page.locator('article').filter({ hasText: slip }).getByText('Write-off approved', { exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath('finance-review.png'), fullPage: true });
  await page.goto('/inventory');
  await expect(page.getByText('Access Restricted', { exact: true })).toBeVisible();
});

test('owner exports the same statement and gets a clean print view', async ({ page }, info) => {
  await login(page, 'owner@karigarflow.com', 'Owner@123');
  await page.goto('/daily-stock');
  await expect(page.getByRole('button', { name: 'Export CSV' })).toBeEnabled();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV' }).click();
  const file = await download;
  const path = await file.path();
  const text = await fs.readFile(path!, 'utf8');
  expect(text).toContain('Company total'); expect(text).toContain('Asia/Kolkata');
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('aside')).not.toBeVisible();
  await page.screenshot({ path: info.outputPath('stock-print.png'), fullPage: true });
  await page.pdf({ path: info.outputPath('stock-print.pdf'), preferCSSPageSize: true, printBackground: true });
});
