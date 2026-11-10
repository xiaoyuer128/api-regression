import importlib.util
from pathlib import Path
import threading
import json
import unittest
from http.server import ThreadingHTTPServer
from test_api_regression import api
import test_extended


class DemoTests(unittest.TestCase):
    def test_demo_and_redaction(self):
        path=Path(__file__).resolve().parents[1]/'examples/demo_service.py'
        spec=importlib.util.spec_from_file_location('demo',path)
        demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
        server=ThreadingHTTPServer(('127.0.0.1',0),demo.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            doc=test_extended.Extended().doc()
            operation=doc['paths']['/items/{id}']['get']
            operation['parameters'][1]['example']='SECRET_QUERY_VALUE'
            operation['responses']['422']={'description':'missing query'}
            doc['paths']['/broken']={'get':{'parameters':[operation['parameters'][1]],'responses':operation['responses']}}
            plan=api.generate(doc)
            report=api.execute(plan,f'http://127.0.0.1:{server.server_port}',True)
            self.assertEqual(report['summary'],{'passed':1,'failed':1,'error':0,'observed':2})
            self.assertNotIn('SECRET_QUERY_VALUE',json.dumps(report))
            self.assertNotIn('wrong-type',json.dumps(report))
            self.assertEqual(report['results'][0]['path'],'/items/{id}')
            self.assertEqual(report['results'][2]['errors'][0]['validator'],'type')
        finally:
            server.shutdown();server.server_close();thread.join()
