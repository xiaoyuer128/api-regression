"""Small runnable inventory service with a deliberate contract regression. Not a production project."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url=urlsplit(self.path)
        if url.path not in ('/items/2','/broken'):
            code,body=404,{'error':'not found'}
        elif 'q' not in parse_qs(url.query):
            code,body=422,{'error':'q required'}
        else:
            code,body=200,{'id':'wrong-type' if url.path=='/broken' else 2}
        self.send_response(code)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
    def log_message(self,*args): pass


if __name__=='__main__':
    print('Inventory demo listening on http://127.0.0.1:8000')
    ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
