"""Pinned TrackMyRupee consent paths: a fresh isolated browser, then Purpose-specific HTTP probes."""
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
import json
import logging
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit

import httpx

from auditor.probes.assessments import (comparable_ease, consent_enforcement, declined_processing,
                                        declined_signup, withdrawal_data)

PIN = '47990e4f19d7debea70c5d56bab77e3c3f051546'
SINK_ENV = 'DPDP_TMR_SINK_URL'
DB_ENV = 'DPDP_TMR_DB'
MAIL_ENV = 'DPDP_TMR_MAIL_DIR'
SETTLE = float(os.environ.get('DPDP_TMR_SETTLE', '3'))
PURPOSES = (('consent_email', 'Email Address'), ('consent_transactions', 'Financial Transactions'),
            ('consent_device', 'Device and Browser Information'))
ROUTES = {('GET', '/accounts/signup/'), ('POST', '/accounts/signup/'), ('GET', '/accounts/login/'),
          ('POST', '/accounts/login/'), ('POST', '/api/prompts/'), ('GET', '/settings/profile/'),
          ('GET', '/consent/'), ('POST', '/consent/'),
          ('GET', '/settings/consent/withdraw/'), ('POST', '/settings/consent/withdraw/')}
ALL_CONSENTS = ('confirm_age', 'consent_email', 'consent_transactions', 'consent_device')
USER_TABLES = ('expenses_userprofile', 'expenses_consentevent', 'expenses_category')
REDIRECTS = (301, 302, 303)
POSTHOG_ID = re.compile(r"\bvar PH_ID = '([0-9a-f]{32})';")
PROFILE = '/settings/profile/'
CONSENT = '/consent/'
VERIFY_PENDING = '/accounts/confirm-email/'
VERIFY_PATH = re.compile(r'/accounts/confirm-email/[-:\w]+/', re.ASCII)
MAIL_URL = re.compile(r'https?://[^\s<>"\']+')
CSRF = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')


def _hide_confirmation_urls(record: logging.LogRecord) -> bool:
    # HTTPX normally logs the full URL at INFO, including the key in this route.
    args = record.args
    if isinstance(args, tuple) and len(args) > 1 and isinstance(args[1], httpx.URL):
        if VERIFY_PATH.fullmatch(args[1].path):
            record.args = (args[0], '/accounts/confirm-email/[masked]/', *args[2:])
    return True


def _verification_path(origin: str, email: str) -> str | None:
    """Read only the synthetic recipient's matching link from a dedicated loopback mailbox."""
    if not (directory := os.environ.get(MAIL_ENV)) or urlsplit(origin).hostname not in ('127.0.0.1', 'localhost', '::1'):
        return None
    paths = set()
    expected_origin = httpx.URL(origin)
    try:
        for file in Path(directory).glob('*.log'):
            if file.is_symlink() or not file.is_file() or file.stat().st_size > 1_000_000:
                continue
            message = BytesParser(policy=policy.default).parsebytes(file.read_bytes())
            recipients = message['To']
            if not recipients or [a.addr_spec for a in recipients.addresses] != [email]:
                continue
            body = message.get_body(preferencelist=('plain', 'html'))
            for link in MAIL_URL.findall(body.get_content() if body else ''):
                parts = urlsplit(link)
                if (VERIFY_PATH.fullmatch(parts.path) and not parts.query and not parts.fragment
                        and httpx.URL(f'{parts.scheme}://{parts.netloc}') == expected_origin):
                    paths.add(parts.path)
    except (OSError, ValueError):
        return None
    return next(iter(paths)) if len(paths) == 1 else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _ProfileForm(HTMLParser):
    def __init__(self, html: str):
        super().__init__()
        self.emails: list[str | None] = []
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            fields = dict(attrs)
            if fields.get('type') == 'email' and fields.get('name') == 'auth_email':
                self.emails.append(fields.get('value'))


def run_browser(origin: str) -> list[dict]:
    script = Path(__file__).with_suffix('.mjs')
    try:
        process = subprocess.run(['node', str(script)],
                                 input=json.dumps({'origin': origin, 'python': sys.executable, 'settle': min(SETTLE, 3)}),
                                 capture_output=True, text=True, timeout=90, check=True)
        data = json.loads(process.stdout)
        if not isinstance(data, dict):
            raise ValueError('Unexpected browser result')
        stage = data.get('stage')
        before = data.get('before') is True and data.get('withdrawn') is True
        after = data.get('after') if isinstance(data.get('after'), bool) else None
        grant = data.get('grant') if type(data.get('grant')) is int else None
        withdrawal = data.get('withdrawal') if type(data.get('withdrawal')) is int else None
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        before, after, grant, withdrawal = False, None, None, None
        stage = 'browser'
    enforcement = consent_enforcement(before, after)
    stage_reason = {
        'browser': 'The Playwright browser did not run',
        'signup': 'The browser did not establish a successful signup',
        'verification': 'The browser did not complete email confirmation and sign-in',
        'profile': 'The authenticated browser profile did not establish Auditor ownership; no withdrawal POST was sent',
        'consent': 'The browser did not complete the required consent form; no withdrawal POST was sent',
        'withdrawal-form': 'The browser could not open the Withdrawal Path',
        'withdrawal-ownership': 'The browser profile did not establish Auditor ownership immediately before withdrawal; no withdrawal POST was sent',
        'withdrawal-post': 'The browser did not observe an accepted withdrawal POST',
        'post-withdrawal': 'The browser did not establish profile availability after withdrawal',
    }.get(stage)
    if enforcement[0] == 'inconclusive' and stage_reason:
        enforcement = ('inconclusive', stage_reason)
    if grant is not None and withdrawal is not None:
        ease = ('inconclusive', f'Grant recorded {grant} interactions and withdrawal {withdrawal}; the Report does not establish a common starting point or Purpose link')
    else:
        ease = comparable_ease(None, None)
        if stage_reason:
            ease = (ease[0], f'{ease[1]}: {stage_reason[0].lower()}{stage_reason[1:]}')
    return [
        {'assertion': 'consent-after-withdrawal', 'finding_id': None, 'result': enforcement[0],
         'method': 'POST', 'route': '/settings/consent/withdraw/', 'reason': enforcement[1],
         'request': 'Auditor-created account; values: [masked]',
         'response': 'Account profile availability compared before and after withdrawal; values: [masked]',
         'criterion': 'enforced server-side'},
        {'assertion': 'comparable-ease', 'finding_id': None, 'result': ease[0],
         'method': 'BROWSER', 'route': '/accounts/signup/ → /settings/consent/withdraw/',
         'reason': ease[1], 'request': 'Signup and withdrawal interactions; values: [masked]',
         'response': 'Counts include clicks and checkbox changes, excluding text entry',
         'criterion': 'withdrawable with comparable ease'},
    ] + run_consent(origin, os.environ.get(SINK_ENV), os.environ.get(DB_ENV))


class Session:
    """One Auditor-owned browser-like client. Fixed routes only; no redirects; bounded requests."""

    def __init__(self, origin: str, limit: int = 40):
        self.origin, self.limit, self.count = origin, limit, 0
        self.client = httpx.Client(follow_redirects=False, trust_env=False, timeout=8)
        self.verification_route = None

    def request(self, method: str, route: str, **kwargs) -> httpx.Response:
        if (method, route) not in ROUTES and not (method in ('GET', 'POST') and route == self.verification_route):
            raise ValueError('route is not a registered Live Probe')
        if self.count >= self.limit:
            raise ValueError('Live Probe request limit reached')
        self.count += 1
        headers = {'Referer': self.origin + route, **kwargs.pop('headers', {})}
        return self.client.request(method, self.origin + route, headers=headers, **kwargs)

    def token(self, route: str) -> str | None:
        page = self.request('GET', route)
        if page.status_code != 200:
            return None
        found = CSRF.search(page.text)
        return found.group(1) if found else self.client.cookies.get('csrftoken')

    def analytics_cookie(self, value: str | None):
        if value:
            self.client.cookies.set('tmr_consent', value)

    def authenticated(self) -> bool:
        return 'sessionid' in self.client.cookies

    @staticmethod
    def _profile_matches(response: httpx.Response, username: str) -> bool:
        return response.status_code == 200 and _ProfileForm(response.text).emails == [f'{username}@example.invalid']

    def owned_profile(self, username: str, *, grant_if_required: bool = False) -> str | None:
        if not self.authenticated():
            return None
        response = self.request('GET', PROFILE)
        if grant_if_required and response.status_code in REDIRECTS and response.headers.get('Location') == CONSENT:
            # Only called in the same session as the successful, synthetic signup or login.
            token = self.token(CONSENT)
            if not token:
                return None
            grant = self.request('POST', CONSENT, data={
                'csrfmiddlewaretoken': token, **dict.fromkeys(ALL_CONSENTS, 'on'),
            })
            if grant.status_code not in REDIRECTS:
                return None
            response = self.request('GET', PROFILE)
        if self._profile_matches(response, username):
            return response.text
        return None

    def close(self):
        self.client.close()


class Sink:
    """Loopback counter for PostHog events scoped to a synthetic account and action window."""

    def __init__(self, url: str | None):
        self.url = None
        if url:
            parts = urlsplit(url)
            if parts.scheme == 'http' and parts.hostname in ('127.0.0.1', 'localhost', '::1') and not parts.username:
                self.url = f'http://{parts.netloc}/'

    def count(self, distinct_id: str, since: str, until: str) -> int | None:
        if not self.url:
            return None
        scope = {'distinct_id': distinct_id, 'since': since, 'until': until}
        try:
            response = httpx.get(self.url, headers={
                'X-DPDP-Distinct-Id': distinct_id, 'X-DPDP-Since': since, 'X-DPDP-Until': until,
            }, timeout=3, trust_env=False)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError):
            return None
        if not isinstance(payload, dict) or any(payload.get(key) != value for key, value in scope.items()):
            return None
        count = payload.get('count')
        return count if type(count) is int and count >= 0 else None


class Rows:
    """Read-only counts of rows owned by an Auditor-created username."""

    def __init__(self, path: str | None):
        self.path = path

    def _connect(self):
        return sqlite3.connect(f'file:{self.path}?mode=ro', uri=True, timeout=3)

    def user_id(self, username: str) -> int | None:
        if not self.path:
            return None
        try:
            with self._connect() as db:
                row = db.execute('SELECT id FROM auth_user WHERE username = ?', (username,)).fetchone()
            return row[0] if row else 0
        except sqlite3.Error:
            return None

    def remaining(self, username: str, user_id: int | None) -> int | None:
        """Rows still linked to the account: the user row plus rows referencing its former id."""
        if not self.path or not user_id:
            return None
        try:
            with self._connect() as db:
                total = db.execute('SELECT COUNT(*) FROM auth_user WHERE username = ?', (username,)).fetchone()[0]
                for table in USER_TABLES:
                    total += db.execute(f'SELECT COUNT(*) FROM {table} WHERE user_id = ?', (user_id,)).fetchone()[0]
            return total
        except sqlite3.Error:
            return None


def _signup(session: Session, username: str, password: str, omit: str | None = None, cookie: str | None = None) -> str:
    """Returns created, verification, rejected, limited or unknown."""
    token = session.token('/accounts/signup/')
    if not token:
        return 'unknown'
    form = {'csrfmiddlewaretoken': token, 'username': username, 'email': f'{username}@example.invalid',
            'password1': password, 'password2': password}
    form.update({name: 'on' for name in ALL_CONSENTS if name != omit})
    session.analytics_cookie(cookie)
    response = session.request('POST', '/accounts/signup/', data=form)
    if response.status_code == 429:
        return 'limited'
    if response.status_code in REDIRECTS and response.headers.get('Location') == VERIFY_PENDING:
        return 'verification'
    if response.status_code in REDIRECTS and session.authenticated():
        return 'created'
    if response.status_code == 200 and not session.authenticated():
        return 'rejected'
    return 'unknown'


def _finish_signup(session: Session, username: str, password: str) -> str | None:
    email = f'{username}@example.invalid'
    route = _verification_path(session.origin, email)
    if route is None:
        return 'Email verification was required but no matching loopback confirmation link was available'
    logging.getLogger('httpx').addFilter(_hide_confirmation_urls)
    session.verification_route = route
    try:
        form = session.request('GET', route)
        token = CSRF.search(form.text) if form.status_code == 200 else None
        if not token or f'href="mailto:{email}"' not in form.text or f'action="{route}"' not in form.text:
            return 'The email confirmation form did not match the Auditor-created account'
        if session.request('POST', route, data={'csrfmiddlewaretoken': token[1]}).status_code not in REDIRECTS:
            return 'The Target Application did not accept email confirmation'
    finally:
        session.verification_route = None
    session.client.cookies.clear()
    if _login(session, username, password, cookie='declined') is not True:
        return 'The Auditor-created account did not authenticate after email confirmation'
    return None


def _login(session: Session, username: str, password: str, cookie: str | None = None) -> bool | None:
    token = session.token('/accounts/login/')
    if not token:
        return None
    session.analytics_cookie(cookie)
    response = session.request('POST', '/accounts/login/', data={
        'csrfmiddlewaretoken': token, 'login': username, 'password': password})
    if response.status_code in REDIRECTS and response.headers.get('Location') == VERIFY_PENDING:
        return None
    if response.status_code in REDIRECTS and session.authenticated():
        return True
    if response.status_code == 200 and not session.authenticated():
        return False
    return None


def _choose(session: Session, value: str) -> bool:
    """Record the cookie-banner choice with the request the banner itself sends."""
    token = session.client.cookies.get('csrftoken')
    response = session.request('POST', '/api/prompts/', headers={'X-CSRFToken': token or '', 'Content-Type': 'application/json'},
                               content=json.dumps({'key': 'cookie', 'action': 'choice', 'value': value}))
    if response.status_code != 200:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return isinstance(payload, dict) and payload.get('status') == 'success'


def _analytics_login(origin: str, username: str, password: str, choice: str,
                     distinct_id: str) -> tuple[str, str] | None:
    session = Session(origin)
    try:
        started = _now()
        if _login(session, username, password, cookie=choice) is not True:
            return None
        finished = _now()
        profile = session.owned_profile(username)
        scope = POSTHOG_ID.search(profile) if profile is not None else None
        return (started, finished) if scope and scope[1] == distinct_id else None
    finally:
        session.close()


def _analytics(session: Session, sink: Sink, username: str, password: str,
               signup: tuple[str, str], profile: str) -> tuple[tuple[str, str], tuple[str, str]]:
    if not sink.url:
        verdict = ('inconclusive', 'A scoped loopback analytics receiver was unavailable')
        return verdict, verdict
    scope = POSTHOG_ID.search(profile)
    if not scope:
        verdict = ('inconclusive', 'The authenticated profile did not expose a PostHog identifier for scoped observation')
        return verdict, verdict
    distinct_id = scope[1]
    declined = _analytics_login(session.origin, username, password, 'declined', distinct_id)
    if not _choose(session, 'accepted'):
        verdict = ('inconclusive', 'The Target Application did not record acceptance of the analytics cookie')
        return verdict, verdict
    granted = _analytics_login(session.origin, username, password, 'accepted', distinct_id)
    recorded_decline = _choose(session, 'declined')
    withdrawn = _analytics_login(session.origin, username, password, 'declined', distinct_id) if recorded_decline else None
    if granted is None:
        verdict = ('inconclusive', 'The granted control did not authenticate with the expected account and PostHog identifier')
        return verdict, verdict
    # The SDK batches asynchronously. Compare producer timestamps, not delivery order.
    time.sleep(SETTLE)
    control = sink.count(distinct_id, *granted)
    if control is None:
        verdict = ('inconclusive', 'The scoped count for the granted control was unavailable')
        return verdict, verdict
    before_withdrawal = None
    if declined is not None:
        signup_hits = sink.count(distinct_id, *signup)
        login_hits = sink.count(distinct_id, *declined)
        if signup_hits is not None and login_hits is not None:
            before_withdrawal = signup_hits + login_hits
    after_withdrawal = sink.count(distinct_id, *withdrawn) if withdrawn is not None else None
    before_verdict = (declined_processing(control, before_withdrawal) if declined is not None else
                      ('inconclusive', 'The declined login did not establish the same account and PostHog identifier'))
    after_verdict = (declined_processing(control, after_withdrawal) if withdrawn is not None else
                     ('inconclusive', 'The withdrawn login did not establish the same account and PostHog identifier'
                      if recorded_decline else 'The Target Application did not record withdrawal of the analytics cookie'))
    return before_verdict, after_verdict


def _withdraw_account(session: Session, rows: Rows, username: str, password: str) -> tuple[str, str]:
    before_id = rows.user_id(username)
    route = '/settings/consent/withdraw/'
    token = session.token(route)
    if not token:
        return 'inconclusive', 'The account withdrawal form was unavailable; no withdrawal POST was sent'
    if session.owned_profile(username) is None:
        return 'inconclusive', 'The authenticated profile did not establish Auditor ownership; no withdrawal POST was sent'
    answer = session.request('POST', route, data={'csrfmiddlewaretoken': token})
    if answer.status_code not in REDIRECTS:
        return 'inconclusive', 'Account withdrawal was not established'
    time.sleep(min(SETTLE, 3))
    session.client.cookies.clear()
    authenticates = _login(session, username, password)
    if authenticates is True and session.owned_profile(username) is None:
        authenticates = None
    return withdrawal_data(authenticates, rows.remaining(username, before_id))


def _outcome(assertion: str, verdict: tuple[str, str], method: str, route: str, request: str, response: str,
             purpose: str) -> dict:
    return {'assertion': assertion, 'finding_id': None, 'result': verdict[0], 'method': method, 'route': route,
            'reason': verdict[1], 'request': request, 'response': response, 'purpose': purpose,
            'criterion': 'enforced server-side'}


def run_consent(origin: str, sink_url: str | None = None, db_path: str | None = None) -> list[dict]:
    """Purpose-specific enforcement probes on Auditor-created accounts only.

    Outcomes are tri-state. Declining a mandatory-bundled consent at signup, analytics
    processing after a decline or withdrawal, and rows after withdrawal are assessed; each
    result is positive Evidence only when the observation was actually made."""
    sink, rows = Sink(sink_url), Rows(db_path)
    username = f'dpdp{secrets.token_hex(16)}'
    password = secrets.token_urlsafe(24)
    outcomes: list[dict] = []
    control = 'unknown'
    declined = {}
    setup_error = None
    analytics_declined = analytics_withdrawn = None
    withdrawal = None
    session = Session(origin)
    withdrawal_started = False
    try:
        # Account 1: every signup consent supplied, with the separate analytics choice declined.
        signup_start = _now()
        control = _signup(session, username, password, cookie='declined')
        signup = (signup_start, _now())
        for field, _ in PURPOSES:
            other = Session(origin)
            try:
                other_name, other_password = f'dpdp{secrets.token_hex(16)}', secrets.token_urlsafe(24)
                attempt = _signup(other, other_name, other_password, omit=field)
                if attempt == 'verification' and _finish_signup(other, other_name, other_password) is None:
                    attempt = 'created'
                declined[field] = attempt
            finally:
                other.close()
        if control == 'verification':
            setup_error = _finish_signup(session, username, password)
            if setup_error is None:
                control = 'created'
        if control == 'created':
            profile = session.owned_profile(username, grant_if_required=True)
            if profile is None:
                setup_error = 'The authenticated profile did not establish Auditor ownership after signup and any required consent'
            else:
                try:
                    analytics_declined, analytics_withdrawn = _analytics(session, sink, username, password, signup, profile)
                except (httpx.HTTPError, ValueError):
                    analytics_declined = analytics_withdrawn = ('inconclusive', 'An expected analytics request did not respond successfully')
                withdrawal_started = True
                withdrawal = _withdraw_account(session, rows, username, password)
    except (httpx.HTTPError, ValueError):
        setup_error = 'An expected TrackMyRupee route did not respond successfully'
    finally:
        session.close()

    for field, label in PURPOSES:
        verdict = declined_signup(control == 'created', declined.get(field) == 'created', declined.get(field) == 'rejected')
        outcomes.append(_outcome(f'consent-declined:{field}', verdict, 'POST', '/accounts/signup/',
                                 f'Auditor-created signup omitting the "{label}" consent; values: [masked]',
                                 'Signup response status and, when required, email confirmation and login; values: [masked]', label))
    channel = 'Local count of PostHog events for the verified account and action window'
    reason = setup_error or 'The control signup did not establish an Auditor-created account'
    unavailable = ('inconclusive', reason)
    outcomes.append(_outcome(
        'analytics-declined', analytics_declined or unavailable, 'POST', '/accounts/signup/ → /accounts/login/',
        'Signup and login with the tmr_consent=declined cookie; values: [masked]',
        f'{channel}; no payloads retained by the Auditor', 'Analytics'))
    outcomes.append(_outcome(
        'analytics-withdrawn', analytics_withdrawn or unavailable, 'POST', '/api/prompts/ → /accounts/login/',
        'Cookie choice accepted, then declined as the banner records it, then login; values: [masked]',
        f'{channel}; no payloads retained by the Auditor', 'Analytics'))
    outcomes.append(_outcome(
        'withdrawal-data-removal', withdrawal or ('inconclusive', reason if withdrawal_started else f'{reason}; no withdrawal POST was sent'),
        'POST', '/settings/consent/withdraw/',
        'Withdrawal POST requires the authenticated profile to match the Auditor-created account; values: [masked]',
        'When sent: post-withdrawal authentication and read-only count of account-linked rows; values: [masked]', 'Account'))
    return outcomes


if __name__ == '__main__':
    # Private stdin/stdout exchange with the isolated Playwright process.
    verification = json.load(sys.stdin)
    print(_verification_path(verification['origin'], verification['email']) or '')
