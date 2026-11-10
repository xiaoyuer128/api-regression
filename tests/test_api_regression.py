from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
from pathlib import Path
import threading
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/api_regression.py'
spec=importlib.util.spec_from_file_location('api_regression',path)
api=importlib.util.module_from_spec(spec); spec.loader.exec_module(api)


class Tests(unittest.TestCase):
    def doc(self, operation=None):
        return {'openapi':'3.0.3','paths':{'/health':{'get':operation or {'responses':{'200':{'description':'ok'}}}}}}

    def test_plan(self):
        plan=api.generate(self.doc())
        self.assertEqual(plan['cases'][0]['expected_statuses'],[200])

    def test_skip(self):
        for op in ({'parameters':[{}],'responses':{'200':{}}},{'security':[{}],'responses':{'200':{}}},{'responses':{'default':{}}}):
            self.assertEqual(len(api.generate(self.doc(op))['skipped']),1)

    def test_version(self):
        with self.assertRaises(ValueError): api.generate({'openapi':'3.1.0'})

    def test_authorization_and_host(self):
        for host, approval in [('http://127.0.0.1',False),('https://example.com',True),('http://127.0.0.1/a',True)]:
            with self.assertRaises(ValueError): api.execute(api.generate(self.doc()),host,approval)

    def test_live_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302 if self.path=='/redirect' else 200)
                if self.path=='/redirect': self.send_header('Location','/health')
                self.end_headers()
            def log_message(self,*args): pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            plan=api.generate(self.doc())
            self.assertEqual(api.execute(plan,base,True)['results'][0]['verdict'],'passed')
            plan['cases'][0]['expected_statuses']=[201]
            self.assertEqual(api.execute(plan,base,True)['results'][0]['verdict'],'failed')
            plan['cases'][0].update(path='/redirect',expected_statuses=[302])
            self.assertEqual(api.execute(plan,base,True)['results'][0]['status'],302)
        finally:
            server.shutdown();server.server_close();thread.join()
