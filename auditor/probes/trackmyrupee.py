"""Pinned TrackMyRupee consent paths: a fresh isolated browser, then Purpose-specific HTTP probes."""
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import secrets
import sqlite3
import subprocess
import time
from urllib.parse import urlsplit

import httpx

from auditor.probes.assessments import (comparable_ease, consent_enforcement, declined_processing,
                                        declined_signup, withdrawal_data)

PIN = '47990e4f19d7debea70c5d56bab77e3c3f051546'
SINK_ENV = 'DPDP_TMR_SINK_URL'
DB_ENV = 'DPDP_TMR_DB'
SETTLE = float(os.environ.get('DPDP_TMR_SETTLE', '3'))
PURPOSES = (('consent_email', 'Email Address'), ('consent_transactions', 'Financial Transactions'),
            ('consent_device', 'Device and Browser Information'))
ROUTES = {('GET', '/accounts/signup/'), ('POST', '/accounts/signup/'), ('GET', '/accounts/login/'),
          ('POST', '/accounts/login/'), ('POST', '/api/prompts/'), ('GET', '/settings/profile/'),
          ('GET', '/settings/consent/withdraw/'), ('POST', '/settings/consent/withdraw/')}
ALL_CONSENTS = ('confirm_age', 'consent_email', 'consent_transactions', 'consent_device')
USER_TABLES = ('expenses_userprofile', 'expenses_consentevent', 'expenses_category')
REDIRECTS = (301, 302, 303)
POSTHOG_ID = re.compile(r"\bvar PH_ID = '([0-9a-f]{32})';")


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
            if fields.get('name') == 'auth_email':
                self.emails.append(fields.get('value'))


def run_browser(origin: str) -> list[dict]:
    script = Path(__file__).with_suffix('.mjs')
    try:
        process = subprocess.run(['node', str(script)], input=json.dumps({'origin': origin}),
                                 capture_output=True, text=True, timeout=90, check=True)
        data = json.loads(process.stdout)
        before = data.get('before') is True and data.get('withdrawn') is True
        after = data.get('after') if isinstance(data.get('after'), bool) else None
        grant = data.get('grant') if type(data.get('grant')) is int else None
        withdrawal = data.get('withdrawal') if type(data.get('withdrawal')) is int else None
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        before, after, grant, withdrawal = False, None, None, None
    enforcement = consent_enforcement(before, after)
    if grant is not None and withdrawal is not None:
        ease = ('inconclusive', f'Grant recorded {grant} interactions and withdrawal {withdrawal}; the Report does not establish a common starting point or Purpose link')
    else:
        ease = comparable_ease(None, None)
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

    def request(self, method: str, route: str, **kwargs) -> httpx.Response:
        if (method, route) not in ROUTES:
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
        found = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page.text)
        return found.group(1) if found else self.client.cookies.get('csrftoken')

    def analytics_cookie(self, value: str | None):
        if value:
            self.client.cookies.set('tmr_consent', value)

    def authenticated(self) -> bool:
        return 'sessionid' in self.client.cookies

    def owned_profile(self, username: str) -> str | None:
        if not self.authenticated():
            return None
        response = self.request('GET', '/settings/profile/')
        if response.status_code == 200 and _ProfileForm(response.text).emails == [f'{username}@example.invalid']:
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
    """Returns created, rejected, limited or unknown."""
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
    if response.status_code in REDIRECTS and session.authenticated():
        return 'created'
    if response.status_code == 200 and not session.authenticated():
        return 'rejected'
    return 'unknown'


def _login(session: Session, username: str, password: str, cookie: str | None = None) -> bool | None:
    token = session.token('/accounts/login/')
    if not token:
        return None
    session.analytics_cookie(cookie)
    response = session.request('POST', '/accounts/login/', data={
        'csrfmiddlewaretoken': token, 'login': username, 'password': password})
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
               signup: tuple[str, str]) -> tuple[int | None, int | None, int | None]:
    if not sink.url:
        return None, None, None
    profile = session.owned_profile(username)
    scope = POSTHOG_ID.search(profile) if profile is not None else None
    if not scope:
        return None, None, None
    distinct_id = scope[1]
    declined = _analytics_login(session.origin, username, password, 'declined', distinct_id)
    if not _choose(session, 'accepted'):
        return None, None, None
    granted = _analytics_login(session.origin, username, password, 'accepted', distinct_id)
    withdrawn = (_analytics_login(session.origin, username, password, 'declined', distinct_id)
                 if _choose(session, 'declined') else None)
    if granted is None or (declined is None and withdrawn is None):
        return None, None, None
    # The SDK batches asynchronously. Compare producer timestamps, not delivery order.
    time.sleep(SETTLE)
    control = sink.count(distinct_id, *granted)
    if control is None:
        return None, None, None
    before_withdrawal = None
    if declined is not None:
        signup_hits = sink.count(distinct_id, *signup)
        login_hits = sink.count(distinct_id, *declined)
        if signup_hits is not None and login_hits is not None:
            before_withdrawal = signup_hits + login_hits
    after_withdrawal = sink.count(distinct_id, *withdrawn) if withdrawn is not None else None
    return control, before_withdrawal, after_withdrawal


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
    analytics_declined = analytics_control = analytics_withdrawn = None
    withdrawal = 'inconclusive', 'The Auditor-created account or its Withdrawal Path was not established'
    session = Session(origin)
    try:
        # Account 1: every signup consent supplied, with the separate analytics choice declined.
        signup_start = _now()
        control = _signup(session, username, password, cookie='declined')
        signup = (signup_start, _now())
        for field, _ in PURPOSES:
            other = Session(origin)
            try:
                declined[field] = _signup(other, f'dpdp{secrets.token_hex(16)}', secrets.token_urlsafe(24), omit=field)
            finally:
                other.close()
        if control == 'created':
            analytics_control, analytics_declined, analytics_withdrawn = _analytics(session, sink, username, password, signup)
            withdrawal = _withdraw_account(session, rows, username, password)
    except (httpx.HTTPError, ValueError):
        pass
    finally:
        session.close()

    for field, label in PURPOSES:
        verdict = declined_signup(control == 'created', declined.get(field) == 'created', declined.get(field) == 'rejected')
        outcomes.append(_outcome(f'consent-declined:{field}', verdict, 'POST', '/accounts/signup/',
                                 f'Auditor-created signup omitting the "{label}" consent; values: [masked]',
                                 'Signup response status and session issuance only; values: [masked]', label))
    channel = 'Local count of PostHog events for the verified account and action window'
    outcomes.append(_outcome(
        'analytics-declined', declined_processing(analytics_control, analytics_declined), 'POST', '/accounts/signup/ → /accounts/login/',
        'Signup and login with the tmr_consent=declined cookie; values: [masked]',
        f'{channel}; no payloads retained by the Auditor', 'Analytics'))
    outcomes.append(_outcome(
        'analytics-withdrawn', declined_processing(analytics_control, analytics_withdrawn), 'POST', '/api/prompts/ → /accounts/login/',
        'Cookie choice accepted, then declined as the banner records it, then login; values: [masked]',
        f'{channel}; no payloads retained by the Auditor', 'Analytics'))
    outcomes.append(_outcome(
        'withdrawal-data-removal', withdrawal, 'POST', '/settings/consent/withdraw/',
        'Withdrawal POST requires the authenticated profile to match the Auditor-created account; values: [masked]',
        'When sent: post-withdrawal authentication and read-only count of account-linked rows; values: [masked]', 'Account'))
    return outcomes
