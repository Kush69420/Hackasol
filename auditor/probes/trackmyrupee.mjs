// TrackMyRupee's pinned signup and withdrawal paths only. No traces or raw traffic are saved.
import { spawnSync } from 'node:child_process';
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
const pending = '/accounts/confirm-email/';
const profilePath = '/settings/profile/';
const withdrawPath = '/settings/consent/withdraw/';
const safeGet = new Set(['/', '/accounts/signup/', '/accounts/login/', pending, '/consent/',
  '/dashboard/', '/settings/', profilePath, withdrawPath, '/favicon.ico']);
const redirects = [301, 302, 303];
const allConsents = ['consent_email', 'consent_transactions', 'consent_device', 'confirm_age'];
let owned = false, signupSent = false, loginArmed = false, withdrawArmed = false;
let grantArmed = false, verificationRoute = null, verifyArmed = false;
let grant = 0, withdrawal = 0, before = false, withdrawn = false, after = null, stage = 'browser';
let browser;
try {
  browser = await chromium.launch({ headless: true });
  // Tall enough that the fixed cookie banner cannot cover the Withdrawal Path's submit button.
  const context = await browser.newContext({ serviceWorkers: 'block', viewport: { width: 1280, height: 1400 } });
  let actions = 0, assets = 0;
  await context.route('**/*', async route => {
    const req = route.request();
    const url = new URL(req.url());
    if (url.origin !== origin || url.username || url.password) return route.abort();
    const read = req.method() === 'GET' || req.method() === 'HEAD';
    const staticPath = url.pathname.startsWith('/static/');
    if (read && !safeGet.has(url.pathname) && url.pathname !== verificationRoute && !staticPath) return route.abort();
    const asset = read && staticPath && !['document', 'xhr', 'fetch'].includes(req.resourceType());
    // The app repeats styles, scripts and fonts on each page. They cannot spend the action budget.
    if (asset ? ++assets > 320 : ++actions > 160) return route.abort();
    if (!read) {
      const form = new URLSearchParams(req.postData() || '');
      const signup = req.method() === 'POST' && url.pathname === '/accounts/signup/' && !signupSent &&
        form.get('username') === username && form.get('email') === email && form.get('password1') === password && form.get('password2') === password;
      const login = req.method() === 'POST' && url.pathname === '/accounts/login/' && loginArmed &&
        form.get('login') === email && form.get('password') === password;
      const consent = req.method() === 'POST' && url.pathname === '/consent/' && grantArmed &&
        allConsents.every(name => form.get(name) === 'on');
      const verify = req.method() === 'POST' && url.pathname === verificationRoute && verifyArmed;
      const withdraw = req.method() === 'POST' && url.pathname === withdrawPath && owned && withdrawArmed;
      if (!(signup || login || consent || verify || withdraw)) return route.abort();
      if (signup) signupSent = true;
      if (login) loginArmed = false;
      if (consent) grantArmed = false;
      if (verify) verifyArmed = false;
      if (withdraw) withdrawArmed = false;
    }
    return route.continue();
  });
  const page = await context.newPage();
  page.setDefaultTimeout(8000);
  const submit = async (route, button) => {
    const [response] = await Promise.all([
      page.waitForResponse(r => r.request().method() === 'POST' && new URL(r.url()).pathname === route),
      button.click(),
    ]);
    return response;
  };
  const login = async () => {
    await page.goto(origin + '/accounts/login/', { waitUntil: 'domcontentloaded' });
    await page.locator('[name="login"]').fill(email);
    await page.locator('[name="password"]').fill(password);
    loginArmed = true;
    return submit('/accounts/login/', page.locator('form.login button[type="submit"]'));
  };
  const checkProfile = async target => {
    const response = await target.goto(origin + profilePath, { waitUntil: 'domcontentloaded' });
    if (response?.status() !== 200 || target.url() !== origin + profilePath) return false;
    const field = target.locator('input[type="email"][name="auth_email"]');
    return await field.count() === 1 && await field.inputValue() === email;
  };
  stage = 'signup';
  await page.goto(origin + '/accounts/signup/', { waitUntil: 'domcontentloaded' });
  await page.locator('[name="username"]').fill(username);
  await page.locator('[name="email"]').fill(email);
  await page.locator('[name="password1"]').fill(password);
  await page.locator('[name="password2"]').fill(password);
  await page.locator('#btn_continue').click(); grant++;
  await page.locator('#id_confirm_age').check(); grant++;
  const signupResponse = await submit('/accounts/signup/', page.locator('#btn_submit_consent'));
  grant++;
  if (!redirects.includes(signupResponse.status())) throw new Error();
  if (await signupResponse.headerValue('location') === pending) {
    stage = 'verification';
    const link = spawnSync(input.python, ['-m', 'auditor.probes.trackmyrupee'], {
      input: JSON.stringify({ origin, email }), encoding: 'utf8', timeout: 5000,
    });
    const route = link.status === 0 ? link.stdout.trim() : '';
    if (!/^\/accounts\/confirm-email\/[-:\w]+\/$/.test(route)) throw new Error();
    verificationRoute = route;
    const verification = await page.goto(origin + route, { waitUntil: 'domcontentloaded' });
    const matchingRecipient = page.locator(`a[href="mailto:${email}"]`);
    if (verification?.status() !== 200 || await matchingRecipient.count() !== 1) throw new Error();
    // The Target signs the key with a timestamp on every render, so after a second boundary the form
    // action carries a fresh signature. Post to that action, but only for the mailed link's own account key.
    const confirmForm = page.locator('form[action^="/accounts/confirm-email/"]');
    const action = await confirmForm.count() === 1 ? await confirmForm.getAttribute('action') : '';
    const accountKey = p => p.split('/')[3].split(':')[0];
    if (!/^\/accounts\/confirm-email\/[-:\w]+\/$/.test(action) || accountKey(action) !== accountKey(route)) throw new Error();
    verificationRoute = action;
    verifyArmed = true;
    const confirmed = await submit(action, confirmForm.locator('button[type="submit"]'));
    verificationRoute = null;
    if (!redirects.includes(confirmed.status())) throw new Error();
    await context.clearCookies();
    if (!redirects.includes((await login()).status())) throw new Error();
  }
  stage = 'profile';
  before = await checkProfile(page);
  if (!before && page.url() === origin + '/consent/' &&
      (await context.cookies(origin)).some(cookie => cookie.name === 'sessionid')) {
    stage = 'consent';
    await page.locator('#id_confirm_age').check(); grant++;
    grantArmed = true;
    const consent = await submit('/consent/', page.locator('#btn_submit_consent'));
    grant++;
    if (!redirects.includes(consent.status())) throw new Error();
    stage = 'profile';
    before = await checkProfile(page);
  }
  if (!before) throw new Error();
  stage = 'withdrawal-form';
  await page.goto(origin + '/settings/', { waitUntil: 'domcontentloaded' });
  await page.locator(`a[href="${withdrawPath}"]:visible`).click();
  withdrawal++;
  if (page.url() !== origin + withdrawPath) throw new Error();
  stage = 'withdrawal-ownership';
  // Check the authenticated profile again, immediately before the destructive POST.
  const identity = await context.newPage();
  try {
    owned = await checkProfile(identity);
  } finally {
    await identity.close();
  }
  if (!owned) throw new Error();
  stage = 'withdrawal-post';
  withdrawArmed = true;
  const withdrawalResponse = await submit(withdrawPath, page.locator('form[method="post"]:not([action]) button[type="submit"]'));
  withdrawal++;
  withdrawn = redirects.includes(withdrawalResponse.status());
  if (!withdrawn) throw new Error();
  stage = 'post-withdrawal';
  await new Promise(resolve => setTimeout(resolve, input.settle * 1000));
  await context.clearCookies();
  const loginResponse = await login();
  if (redirects.includes(loginResponse.status())) {
    if (await checkProfile(page)) after = true;
  } else if (loginResponse.status() === 200 && page.url() === origin + '/accounts/login/' &&
      await page.locator('form.login .alert-danger').count() === 1) {
    after = false;
  }
  if (after !== null) stage = null;
} catch (_) {
  // Failed setup/interaction never becomes a positive assertion.
} finally {
  if (browser) await browser.close();
}
process.stdout.write(JSON.stringify({ before, withdrawn, after, stage, grant: before ? grant : null,
  withdrawal: withdrawn ? withdrawal : null }));
