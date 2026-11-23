"""Small dedicated consent workflow for browser interaction tests."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


class Server(ThreadingHTTPServer):
    def __init__(self, *, enforced, images=0, profile_mismatch=False):
        super().__init__(('127.0.0.1', 0), Handler)
        self.enforced = enforced
        self.images, self.profile_mismatch = images, profile_mismatch
        self.withdrawal_form_read = False
        self.account = None
        self.withdrawn = False


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

    def do_GET(self):
        if self.path == '/accounts/signup/':
            images = ''.join(f'<img src="/static/probe-{i}.png">' for i in range(self.server.images))
            return self.send(images + '''<form method="post" action="/accounts/signup/">
                <input name="username"><input name="email"><input name="password1"><input name="password2">
                <button id="btn_continue" type="button">Continue</button>
                <input type="checkbox" id="id_confirm_age" name="confirm_age">
                <button id="btn_submit_consent" type="submit" disabled>Grant</button></form>
                <script>addEventListener('load', () => document.getElementById('btn_submit_consent').disabled = false);</script>''')
        if self.path == '/accounts/login/':
            return self.send(self.login_form())
        if self.path == '/settings/profile/':
            if (self.server.account and 'sessionid=fixture-active' in self.headers.get('Cookie', '')
                    and (not self.server.withdrawn or not self.server.enforced)):
                email = self.server.account['email']
                value = 'other@example.invalid' if self.server.profile_mismatch and self.server.withdrawal_form_read else email
                return self.send(f'<p>{email}</p><input type="email" name="auth_email" value="{value}">')
            return self.send('', 302, [('Location', '/accounts/login/')])
        if self.path == '/settings/':
            return self.send('<a href="/settings/consent/withdraw/">Withdraw</a>')
        if self.path == '/settings/consent/withdraw/':
            self.server.withdrawal_form_read = True
            return self.send('''<form method="post" action="/accounts/logout/" hidden>
                <button type="submit">Logout</button></form>
                <form method="post"><button type="submit">Withdraw</button></form>''')
        if self.path.startswith('/static/probe-'):
            return self.send('', 404)
        return self.send('not found', 404)

    @staticmethod
    def login_form(error=False):
        warning = '<p class="alert-danger">Sign-in rejected</p>' if error else ''
        return f'''<form class="login" method="post" action="/accounts/login/">{warning}
            <input name="login"><input name="password"><button type="submit">Login</button></form>'''

    def do_POST(self):
        data = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode())
        if self.path == '/accounts/signup/':
            self.server.account = {key: data[key][0] for key in ('username', 'email', 'password1')}
            return self.send('', 302, [('Location', '/settings/profile/'),
                                       ('Set-Cookie', 'sessionid=fixture-active; Path=/')])
        if self.path == '/settings/consent/withdraw/':
            self.server.withdrawn = True
            return self.send('', 302, [('Location', '/accounts/login/')])
        if self.path == '/accounts/login/':
            account = self.server.account
            if (account and data.get('login') == [account['email']] and data.get('password') == [account['password1']]
                    and not (self.server.enforced and self.server.withdrawn)):
                return self.send('', 302, [('Location', '/settings/profile/'),
                                           ('Set-Cookie', 'sessionid=fixture-active; Path=/')])
            return self.send(self.login_form(error=True))
        return self.send('not found', 404)
