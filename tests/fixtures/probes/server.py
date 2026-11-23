"""Disposable, local-only HTTP fixture; all records originate in the test."""
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


class Server(ThreadingHTTPServer):
    def __init__(self, *, exposed=True, nested=True, erases=False):
        super().__init__(("127.0.0.1", 0), Handler)
        self.exposed, self.nested, self.erases = exposed, nested, erases
        self.accounts, self.tokens, self.memories = {}, {}, []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, status, data, headers=()):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for name, value in headers:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(raw)

    def identity(self):
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        if not token:
            token = self.headers.get("Cookie", "").removeprefix("token=")
        return self.server.tokens.get(token)

    def do_GET(self):
        if self.path == '/api/SecurityQuestions':
            return self.send(200, {'data': [{'id': 1}]})
        if self.path == '/dataerasure':
            return self.send(200 if self.identity() else 401, {})
        if self.path != '/rest/memories':
            return self.send(404, {})
        current = self.identity()
        if not self.server.exposed and current is None:
            return self.send(401, {})
        records = []
        for item in self.server.memories:
            if self.server.exposed or item['owner'] == current:
                record = {'caption': item['caption']}
                if self.server.nested:
                    record['User'] = {'email': self.server.accounts[item['owner']]['email']}
                records.append(record)
        return self.send(200, {'data': records}, [('Access-Control-Allow-Origin', '*' if self.server.exposed else 'https://other.invalid')])

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
        if self.path == '/rest/memories':
            current = self.identity()
            found = re.search(br'name="caption"\r\n\r\n([^\r]+)', body)
            if current and found:
                self.server.memories.append({'caption': found.group(1).decode(), 'owner': current})
                return self.send(200, {'data': {}})
            return self.send(401, {})
        if self.path == '/dataerasure':
            current = self.identity()
            if not current:
                return self.send(401, {})
            if self.server.erases:
                del self.server.accounts[current]
            return self.send(200, {})
        data = json.loads(body or b'{}')
        if self.path == '/api/Users':
            ident = len(self.server.accounts) + 1
            self.server.accounts[ident] = {'email': data['email'], 'password': data['password']}
            return self.send(201, {'data': {'id': ident, 'email': data['email']}})
        if self.path == '/api/SecurityAnswers':
            return self.send(201, {'data': {}})
        if self.path == '/rest/user/login':
            for ident, account in self.server.accounts.items():
                if account == data:
                    token = f'synthetic-session-{ident}'
                    self.server.tokens[token] = ident
                    return self.send(200, {'authentication': {'token': token}})
            return self.send(401, {})
        return self.send(404, {})


if __name__ == '__main__':
    server = Server()
    print(server.server_port, flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()
