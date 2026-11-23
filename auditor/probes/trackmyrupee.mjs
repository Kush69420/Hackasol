// TrackMyRupee's pinned signup and withdrawal paths only. No traces or raw traffic are saved.
import { createRequire } from 'node:module';
import { randomBytes } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const { chromium } = require(path.join(root, 'dashboard/frontend/node_modules/playwright'));
const input = JSON.parse(await new Promise(resolve => { let s = ''; process.stdin.on('data', b => s += b); process.stdin.on('end', () => resolve(s)); }));
const origin = new URL(input.origin).origin;
const value = randomBytes(16).toString('hex');
const email = `dpdp-${value}@example.invalid`;
const username = `dpdp${value}`;
const password = randomBytes(24).toString('base64url');
let owned = false, signedUp = false, signupSent = false, loginArmed = false, withdrawArmed = false, grant = 0, withdrawal = 0, before = false, withdrawn = false, after = null;
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ serviceWorkers: 'block' });
  let count = 0;
  await context.route('**/*', async route => {
    const req = route.request();
    const url = new URL(req.url());
    if (++count > 160 || url.origin !== origin || url.username || url.password) return route.abort();
    const safeGet = new Set(['/', '/accounts/signup/', '/accounts/login/', '/settings/', '/settings/profile/', '/settings/consent/withdraw/', '/favicon.ico']);
    if ((req.method() === 'GET' || req.method() === 'HEAD') && !safeGet.has(url.pathname) && !url.pathname.startsWith('/static/')) return route.abort();
    if (req.method() !== 'GET' && req.method() !== 'HEAD') {
      const form = new URLSearchParams(req.postData() || '');
      const signup = req.method() === 'POST' && url.pathname === '/accounts/signup/' && !signupSent &&
        form.get('username') === username && form.get('email') === email && form.get('password1') === password && form.get('password2') === password;
      const login = req.method() === 'POST' && url.pathname === '/accounts/login/' && owned && withdrawn && loginArmed &&
        form.get('login') === email && form.get('password') === password;
      const withdraw = req.method() === 'POST' && url.pathname === '/settings/consent/withdraw/' && owned && withdrawArmed;
      if (!(signup || login || withdraw)) return route.abort();
      if (signup) signupSent = true;
      if (login) loginArmed = false;
      if (withdraw) withdrawArmed = false;
    }
    return route.continue();
  });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  await page.goto(origin + '/accounts/signup/', { waitUntil: 'domcontentloaded' });
  await page.locator('[name="username"]').fill(username);
  await page.locator('[name="email"]').fill(email);
  await page.locator('[name="password1"]').fill(password);
  await page.locator('[name="password2"]').fill(password);
  await page.locator('#btn_continue').click(); grant++;
  await page.locator('#id_confirm_age').check(); grant++;
  const registration = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/accounts/signup/');
  await page.locator('#btn_submit_consent').click(); grant++;
  const signupResponse = await registration;
  signedUp = signupResponse.status() >= 200 && signupResponse.status() < 400;
  if (!signedUp) throw new Error('setup');
  const profile = await page.goto(origin + '/settings/profile/', { waitUntil: 'domcontentloaded' });
  before = !!profile && profile.status() === 200 && (await page.content()).includes(email);
  owned = before;
  if (!owned) throw new Error('setup');
  await page.goto(origin + '/settings/', { waitUntil: 'domcontentloaded' });
  await page.locator('a[href="/settings/consent/withdraw/"]').first().click(); withdrawal++;
  const request = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/settings/consent/withdraw/');
  withdrawArmed = true;
  await page.locator('form[method="post"] button[type="submit"]').click(); withdrawal++;
  const withdrawalResponse = await request;
  withdrawn = withdrawalResponse.status() >= 200 && withdrawalResponse.status() < 400;
  if (!withdrawn) throw new Error('withdrawal');
  let check = await page.goto(origin + '/settings/profile/', { waitUntil: 'domcontentloaded' });
  if (check && check.status() === 200 && (await page.content()).includes(email)) {
    after = true;
  } else {
    await page.goto(origin + '/accounts/login/', { waitUntil: 'domcontentloaded' });
    await page.locator('[name="login"]').fill(email);
    await page.locator('[name="password"]').fill(password);
    const login = page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === '/accounts/login/');
    loginArmed = true;
    await page.locator('form button[type="submit"]').first().click();
    const loginResponse = await login;
    if (loginResponse.status() >= 200 && loginResponse.status() < 400) {
      check = await page.goto(origin + '/settings/profile/', { waitUntil: 'domcontentloaded' });
      if (check && check.status() === 200) after = (await page.content()).includes(email);
    }
  }
} catch (_) {
  // Failed setup/interaction never becomes a positive assertion.
} finally {
  if (browser) await browser.close();
}
process.stdout.write(JSON.stringify({ before, withdrawn, after, grant: owned ? grant : null, withdrawal: withdrawn ? withdrawal : null }));
