import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
def run(args, expected):
    result=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    if result.returncode != expected: raise RuntimeError(result.stdout+result.stderr)
    return {'command':args,'exit_code':result.returncode,'output':json.loads(result.stdout)}
import importlib.util
import threading
from http.server import ThreadingHTTPServer
spec=importlib.util.spec_from_file_location('service',ROOT/'examples/demo_service.py')
service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
spec=importlib.util.spec_from_file_location('runner',ROOT/'scripts/api_regression.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
schema={'type':'object','required':['id'],'properties':{'id':{'type':'integer'}}}
operation={'parameters':[{'in':'query','name':'q','required':True,'example':'demo','schema':{'type':'string'}}],'responses':{'200':{'content':{'application/json':{'schema':schema}}},'422':{'description':'missing query'}}}
doc={'openapi':'3.0.3','paths':{'/items/2':{'get':operation},'/broken':{'get':operation}}}
server=ThreadingHTTPServer(('127.0.0.1',0),service.Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    report=runner.execute(runner.generate(doc),f'http://127.0.0.1:{server.server_port}',True)
    assert report['summary']=={'passed':1,'failed':1,'error':0,'observed':2},report
    results=[report]
finally:
    server.shutdown();server.server_close();thread.join()
print(json.dumps({'results':results,'limitation':'Script demonstration, not independent Agent evaluation.'},ensure_ascii=True,indent=2))
