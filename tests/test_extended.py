import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import unittest
from test_api_regression import api


class Extended(unittest.TestCase):
    def doc(self):
        return {'openapi':'3.0.3','paths':{'/items/{id}':{'get':{'parameters':[{'name':'id','in':'path','required':True,'example':2,'schema':{'type':'integer'}},{'name':'q','in':'query','required':True,'example':'a b&c','schema':{'type':'string'}}],'responses':{'200':{'content':{'application/json':{'schema':{'type':'object','required':['id'],'properties':{'id':{'type':'integer'}}}}}}}}}}}

    def test_parameters(self):
        plan=api.generate(self.doc())
        self.assertEqual(len(plan['cases']),2)
        self.assertEqual(plan['cases'][0]['path'],'/items/2')
        self.assertEqual(plan['cases'][1]['kind'],'exploratory')
        self.assertNotIn('q',plan['cases'][1]['query'])

    def test_skip_unsupported_schema(self):
        doc=self.doc(); doc['paths']['/items/{id}']['get']['responses']['200']['content']['application/json']['schema']['nullable']=True
        self.assertFalse(api.generate(doc)['cases'])

    def test_limits(self):
        doc={'openapi':'3.0.3','paths':{f'/x{i}':{'get':{'responses':{'200':{}}}} for i in range(101)}}
        with self.assertRaises(ValueError): api.generate(doc)
        for timeout in (0,-1,31,float('nan')):
            with self.assertRaises(ValueError): api.execute({'cases':[],'skipped':[]},'http://127.0.0.1',True,timeout)

    def test_path_override(self):
        doc=self.doc(); item=doc['paths']['/items/{id}']; item['parameters']=[{'name':'id','in':'path','required':True,'example':9,'schema':{'type':'integer'}}]
        self.assertEqual(api.generate(doc)['cases'][0]['path'],'/items/2')

    def test_generated_pytest_and_body(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.send_header('Content-Type','application/json'); self.end_headers()
                self.wfile.write(b'{"id":2}')
            def log_message(self,*a): pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            plan=api.generate(self.doc())
            report=api.execute(plan,base,True)
            self.assertEqual([r['verdict'] for r in report['results']],['passed','observed'])
            plan['cases'][0]['response_schemas']['200']['properties']['id']['type']='string'
            self.assertEqual(api.execute(plan,base,True)['results'][0]['verdict'],'failed')
            root=Path(__file__).resolve().parents[1]
            with tempfile.TemporaryDirectory() as tmp:
                spec=Path(tmp)/'spec.json'; output=Path(tmp)/'test_generated.py'
                spec.write_text(json.dumps(self.doc()))
                run=subprocess.run([sys.executable,str(root/'scripts/api_regression.py'),'--spec',str(spec),'--export-pytest',str(output)],capture_output=True)
                self.assertEqual(run.returncode,0,run.stderr)
                env=dict(os.environ,API_REGRESSION_SCRIPT=str(root/'scripts/api_regression.py'),API_REGRESSION_APPROVED='1',API_REGRESSION_BASE_URL=base)
                run=subprocess.run([sys.executable,'-m','pytest','--rootdir',tmp,str(output),'-q'],cwd=tmp,env=env,capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                self.assertIn('1 passed',run.stdout)
        finally:
            server.shutdown();server.server_close();thread.join()
