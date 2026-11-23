"""Small dedicated consent workflow for browser interaction tests."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


class Server(ThreadingHTTPServer):
    def __init__(self, *, enforced):
        super().__init__(('127.0.0.1', 0), Handler)
        self.enforced = enforced
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
            return self.send('''<form method="post" action="/accounts/signup/">
                <input name="username"><input name="email"><input name="password1"><input name="password2">
                <button id="btn_continue" type="button">Continue</button>
                <input type="checkbox" id="id_confirm_age" name="confirm_age">
                <button id="btn_submit_consent" type="submit">Grant</button></form>''')
        if self.path == '/accounts/login/':
            return self.send('''<form method="post"><input name="login"><input name="password">
                <button type="submit">Login</button></form>''')
        if self.path == '/settings/profile/':
            if self.server.account and (not self.server.withdrawn or not self.server.enforced):
                return self.send(self.server.account['email'])
            return self.send('login required')
        if self.path == '/settings/':
            return self.send('<a href="/settings/consent/withdraw/">Withdraw</a>')
        if self.path == '/settings/consent/withdraw/':
            return self.send('<form method="post"><button type="submit">Withdraw</button></form>')
        return self.send('not found', 404)

    def do_POST(self):
        data = parse_qs(self.rfile.read(int(self.headers['Content-Length'])).decode())
        if self.path == '/accounts/signup/':
            self.server.account = {key: data[key][0] for key in ('username', 'email', 'password1')}
            return self.send('', 302, [('Location', '/settings/profile/')])
        if self.path == '/settings/consent/withdraw/':
            self.server.withdrawn = True
            return self.send('', 302, [('Location', '/accounts/login/')])
        if self.path == '/accounts/login/':
            return self.send('login')
        return self.send('not found', 404)
