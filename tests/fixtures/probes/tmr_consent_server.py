"""Recorded-behaviour TrackMyRupee stand-in: routes, status codes and cookies follow the pinned Target.

mode 'enforced'   declined consent is rejected, a declined analytics choice sends nothing, withdrawal erases.
mode 'violating'  declined consent still creates the account, analytics still fires, withdrawal erases nothing.
mode 'limited'    every signup is rate limited (HTTP 429), so no control account exists.
mode 'profile-mismatch'   the authenticated profile changes before withdrawal.
"""
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import sqlite3
from urllib.parse import parse_qs

CONSENTS = ('confirm_age', 'consent_email', 'consent_transactions', 'consent_device')


def distinct_id(username):
    return sha256(username.encode()).hexdigest()[:32]


class Sink(ThreadingHTTPServer):
    def __init__(self, response):
        super().__init__(('127.0.0.1', 0), SinkHandler)
        self.response = response
        self.events = []

    def record(self, scope, at=None):
        self.events.append((scope, at or datetime.now(timezone.utc)))


class SinkHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        scope = {'distinct_id': self.headers.get('X-DPDP-Distinct-Id'),
                 'since': self.headers.get('X-DPDP-Since'), 'until': self.headers.get('X-DPDP-Until')}
        if self.server.response == 'malformed':
            payload = []
        elif self.server.response == 'unscoped' or not all(scope.values()):
            payload = {'count': len(self.server.events)}
        else:
            start, end = (datetime.fromisoformat(scope[k]) for k in ('since', 'until'))
            count = sum(scope['distinct_id'] == key and start <= at < end for key, at in self.server.events)
            payload = {**scope, 'count': count}
            if self.server.response == 'invalid-count':
                payload['count'] = True
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class Server(ThreadingHTTPServer):
    def __init__(self, mode, sink, db_path, *, fail_login=None, noise=False, delayed_control=False):
        super().__init__(('127.0.0.1', 0), Handler)
        self.mode, self.sink, self.db_path = mode, sink, db_path
        self.fail_login, self.noise, self.delayed_control = fail_login, noise, delayed_control
        self.pending_control = None
        self.withdrawal_form_read = False
        self.withdrawal_posts = 0
        db = sqlite3.connect(db_path)
        db.executescript('''CREATE TABLE auth_user (id INTEGER PRIMARY KEY, username TEXT, password TEXT);
            CREATE TABLE expenses_userprofile (id INTEGER PRIMARY KEY, user_id INTEGER);
            CREATE TABLE expenses_consentevent (id INTEGER PRIMARY KEY, user_id INTEGER);
            CREATE TABLE expenses_category (id INTEGER PRIMARY KEY, user_id INTEGER);''')
        db.commit()
        db.close()

    def db(self):
        return sqlite3.connect(self.db_path)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def send(self, body='', status=200, headers=()):
        raw = body.encode()
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(raw)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)

    def cookies(self):
        return dict(part.strip().split('=', 1) for part in self.headers.get('Cookie', '').split(';') if '=' in part)

    def analytics(self, username):
        """The Target's capture call, gated on the tmr_consent cookie only when enforcing."""
        choice = self.cookies().get('tmr_consent')
        if self.server.noise:
            self.server.sink.record('another-account')
        if choice == 'declined' and self.server.pending_control is not None:
            self.server.sink.record(*self.server.pending_control)
            self.server.pending_control = None
        if choice == 'accepted' or (choice == 'declined' and self.server.mode == 'violating'):
            scope = distinct_id(username)
            self.server.sink.record(scope)
            if self.server.delayed_control and choice == 'accepted':
                self.server.pending_control = (scope, datetime.now(timezone.utc))

    def do_GET(self):
        if self.path == '/settings/profile/':
            user_id = self.cookies().get('sessionid', '')[1:]
            with self.server.db() as db:
                row = db.execute('SELECT username FROM auth_user WHERE id = ?', (user_id,)).fetchone()
            if not row:
                return self.send('', 302, [('Location', '/accounts/login/')])
            username = row[0]
            email = f'{username}@example.invalid'
            if self.server.mode == 'profile-mismatch' and self.server.withdrawal_form_read:
                # A stray copy of the expected email does not identify the authenticated profile.
                email = 'different@example.invalid'
            return self.send(f'<p>{username}@example.invalid</p><input name="auth_email" value="{email}">'
                             f"<script>var PH_ID = '{distinct_id(username)}';</script>")
        if self.path == '/settings/consent/withdraw/':
            self.server.withdrawal_form_read = True
        if self.path in ('/accounts/signup/', '/accounts/login/', '/settings/consent/withdraw/'):
            return self.send('<input type="hidden" name="csrfmiddlewaretoken" value="tok">',
                             headers=[('Set-Cookie', 'csrftoken=tok; Path=/')])
        return self.send('not found', 404)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length') or 0)).decode()
        if self.path == '/api/prompts/':
            return self.send('{"status":"success"}', 200)
        data = {key: values[0] for key, values in parse_qs(body).items()}
        if self.path == '/accounts/signup/':
            if self.server.mode == 'limited':
                return self.send('slow down', 429)
            if self.server.mode != 'violating' and not all(name in data for name in CONSENTS):
                return self.send('This consent is required')
            db = self.server.db()
            cursor = db.execute('INSERT INTO auth_user (username, password) VALUES (?, ?)', (data['username'], data['password1']))
            db.execute('INSERT INTO expenses_consentevent (user_id) VALUES (?)', (cursor.lastrowid,))
            db.commit()
            db.close()
            self.analytics(data['username'])
            return self.send('', 302, [('Location', '/dashboard/'), ('Set-Cookie', f'sessionid=s{cursor.lastrowid}; Path=/')])
        if self.path == '/accounts/login/':
            db = self.server.db()
            row = db.execute('SELECT id FROM auth_user WHERE username = ? AND password = ?',
                             (data.get('login'), data.get('password'))).fetchone()
            db.close()
            if not row:
                return self.send('invalid')
            self.analytics(data['login'])
            if self.cookies().get('tmr_consent') == self.server.fail_login and self.server.fail_login is not None:
                return self.send('invalid')
            return self.send('', 302, [('Location', '/dashboard/'), ('Set-Cookie', f'sessionid=s{row[0]}; Path=/')])
        if self.path == '/settings/consent/withdraw/':
            self.server.withdrawal_posts += 1
            user = self.cookies().get('sessionid', '')[1:]
            if self.server.mode == 'enforced' and user:
                db = self.server.db()
                for table in ('expenses_userprofile', 'expenses_consentevent', 'expenses_category'):
                    db.execute(f'DELETE FROM {table} WHERE user_id = ?', (user,))
                db.execute('DELETE FROM auth_user WHERE id = ?', (user,))
                db.commit()
                db.close()
            return self.send('', 302, [('Location', '/accounts/login/')])
        return self.send('not found', 404)
