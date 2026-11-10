"""Generate a narrow OpenAPI status-contract plan; run only on explicit IPv4 loopback."""
import argparse
import json
import time
from pathlib import Path
import urllib.request
import urllib.error
from urllib.parse import urlsplit
from urllib.parse import urlencode, quote
from jsonschema import Draft4Validator
from jsonschema.exceptions import SchemaError


def supported_schema(schema):
    if not isinstance(schema, dict):
        raise ValueError('Schema must be an object')
    allowed = {'type','properties','required','additionalProperties','items','enum','minimum','maximum','minLength','maxLength','minItems','maxItems','pattern','description','example','default','title'}
    if set(schema)-allowed:
        raise ValueError('Unsupported schema keyword')
    Draft4Validator.check_schema(schema)
    for child in schema.get('properties',{}).values(): supported_schema(child)
    if 'items' in schema: supported_schema(schema['items'])
    if isinstance(schema.get('additionalProperties'),dict): supported_schema(schema['additionalProperties'])
    return schema


def parameter_value(parameter):
    schema = supported_schema(parameter.get('schema',{}))
    if schema.get('type') not in ('string','integer','number','boolean'):
        raise ValueError('Only scalar query/path parameters supported')
    if any(k in parameter for k in ('content','examples')) or parameter.get('style','form' if parameter['in']=='query' else 'simple') != ('form' if parameter['in']=='query' else 'simple'):
        raise ValueError('Unsupported parameter serialization')
    if 'example' in parameter: value = parameter['example']
    elif 'example' in schema: value = schema['example']
    elif 'enum' in schema and schema['enum']: value = schema['enum'][0]
    elif 'default' in schema: value = schema['default']
    else: raise ValueError('Parameter requires an explicit valid example, enum or default')
    if not Draft4Validator(schema).is_valid(value):
        raise ValueError('Parameter sample violates schema')
    return str(value).lower() if isinstance(value,bool) else str(value)


def generate(spec):
    if not isinstance(spec, dict) or spec.get('openapi') not in ('3.0.0','3.0.1','3.0.2','3.0.3'):
        raise ValueError('Supported OpenAPI versions: 3.0.0–3.0.3')
    if not isinstance(spec.get('paths'), dict):
        raise ValueError('paths must be an object')
    cases, skipped = [], []
    for path, item in spec['paths'].items():
        if not isinstance(item, dict):
            raise ValueError('Path item must be an object')
        for method, operation in item.items():
            if method.lower() not in ('get','post','put','patch','delete','head','options','trace'):
                continue
            reason = None
            if not isinstance(operation, dict):
                raise ValueError('Operation must be an object')
            if method != 'get':
                reason = 'Only GET is supported'
            elif not path.startswith('/') or path.startswith('//') or any(c in path for c in ('?','#','\\','\r','\n')):
                reason = 'Unsupported path'
            elif '$ref' in item or '$ref' in operation:
                reason = 'References are not supported yet'
            elif operation.get('security', spec.get('security')) or operation.get('requestBody'):
                reason = 'Authentication and request bodies are not supported yet'
            responses = operation.get('responses', {})
            if not isinstance(responses, dict):
                raise ValueError('responses must be an object')
            statuses = sorted(int(code) for code in responses if isinstance(code,str) and len(code)==3 and code.isascii() and code.isdigit() and 100<=int(code)<=599)
            if not statuses or any(code not in [str(s) for s in statuses] for code in responses):
                reason = 'Only explicit numeric response statuses are supported'
            query, actual_path, contracts = {}, path, {}
            parameters = {}
            try:
                for parameter in item.get('parameters',[]) + operation.get('parameters',[]):
                    if not isinstance(parameter,dict) or '$ref' in parameter or parameter.get('in') not in ('path','query') or not isinstance(parameter.get('name'),str):
                        raise ValueError('Unsupported parameter')
                    parameters[(parameter['in'],parameter['name'])] = parameter
                for (location,name), parameter in parameters.items():
                    value = parameter_value(parameter)
                    if location=='query': query[name] = value
                    else:
                        if not parameter.get('required') or '{'+name+'}' not in actual_path:
                            raise ValueError('Invalid path parameter')
                        if value in ('.','..'): raise ValueError('Dot path sample is unsupported')
                        actual_path = actual_path.replace('{'+name+'}',quote(value,safe=''))
                if '{' in actual_path or '}' in actual_path:
                    raise ValueError('Unresolved path template')
                for code,response in responses.items():
                    if not isinstance(response,dict) or '$ref' in response:
                        raise ValueError('Response references unsupported')
                    content = response.get('content',{})
                    if content:
                        if set(content)!={'application/json'} or 'schema' not in content['application/json']:
                            raise ValueError('Only explicit application/json response schemas supported')
                        contracts[code]=supported_schema(content['application/json']['schema'])
            except (ValueError,TypeError,KeyError,SchemaError) as exc:
                reason = str(exc)
            if reason:
                skipped.append({'method':method.upper(),'path':path,'reason':reason})
            else:
                cases.append({'method':'GET','path':actual_path,'path_template':path,'query':query,'expected_statuses':statuses,'response_schemas':contracts,'expectation_source':'OpenAPI responses','kind':'contract'})
                for (location,name),parameter in parameters.items():
                    if location=='query' and parameter.get('required'):
                        cases.append({'method':'GET','path':actual_path,'path_template':path,'query':{k:v for k,v in query.items() if k!=name},'expected_statuses':statuses,'response_schemas':contracts,'expectation_source':'Exploratory missing required query; exact error unspecified','kind':'exploratory'})
    if len(cases)>100:
        raise ValueError('Maximum 100 executable cases')
    return {'version':1,'cases':cases,'skipped':skipped}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def execute(plan, base_url, approved=False, timeout=3):
    if not approved:
        raise ValueError('Explicit --approve-read-only is required')
    url = urlsplit(base_url)
    if url.scheme!='http' or url.hostname!='127.0.0.1' or url.username or url.password or url.path not in ('','/') or url.query or url.fragment:
        raise ValueError('First version supports only http://127.0.0.1[:port]')
    if not 0<timeout<=30 or len(plan['cases'])>100:
        raise ValueError('Invalid timeout or case count')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    results = []
    for index, case in enumerate(plan['cases'],1):
        started=time.monotonic()
        identity={'case_id':f'case-{index:03d}', 'method':'GET', 'path':case.get('path_template','[redacted path]'), 'expected_statuses':case['expected_statuses'], 'reproduce':'Regenerate from the local spec; run only this reviewed case with the same authorized base URL. Parameter values are intentionally omitted.'}
        if case['method']!='GET' or not case['path'].startswith('/') or case['path'].startswith('//'):
            raise ValueError('Unsupported executable case')
        try:
            try:
                query = urlencode(case.get('query',{}))
                response = opener.open(base_url.rstrip('/')+case['path']+('?' + query if query else ''),timeout=timeout)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                status = response.code
                schema = case.get('response_schemas',{}).get(str(status))
                errors = []
                if schema is not None:
                    if response.headers.get_content_type()!='application/json':
                        errors.append('Expected application/json')
                    else:
                        raw=response.read(1048577)
                        if len(raw)>1048576: errors.append('Response exceeds 1 MiB')
                        else:
                            try:
                                body=json.loads(raw.decode('utf-8'))
                                errors.extend({'code':'schema_mismatch','validator':e.validator,'instance_depth':len(e.path),'schema_depth':len(e.schema_path)} for e in Draft4Validator(schema).iter_errors(body))
                            except (ValueError,UnicodeError): errors.append('Invalid JSON response')
            verdict = 'observed' if case.get('kind')=='exploratory' else 'passed' if status in case['expected_statuses'] and not errors else 'failed'
            results.append({**identity,'status':status,'verdict':verdict,'errors':errors,'elapsed_ms':round((time.monotonic()-started)*1000,2)})
        except (OSError, ValueError) as exc:
            results.append({**identity,'verdict':'error','error_type':type(exc).__name__,'elapsed_ms':round((time.monotonic()-started)*1000,2)})
    return {'results':results,'skipped':plan['skipped'],'summary':{v:sum(r['verdict']==v for r in results) for v in ('passed','failed','error','observed')},'scope':'GET status and supported JSON schema subset; exploratory outcomes are observations'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',required=True)
    parser.add_argument('--base-url')
    parser.add_argument('--approve-read-only',action='store_true')
    parser.add_argument('--timeout',type=float,default=3)
    parser.add_argument('--export-pytest',help='Write a portable test file; no execution')
    args=parser.parse_args()
    try:
        plan=generate(json.loads(Path(args.spec).read_text(encoding='utf-8')))
        if args.export_pytest:
            if Path(args.export_pytest).resolve()==Path(args.spec).resolve(): raise ValueError('Cannot overwrite specification')
            if args.base_url: raise ValueError('Export and execution are separate operations')
            source = "import json, os\nfrom pathlib import Path\nimport importlib.util\nimport pytest\nmodule_path = Path(os.environ['API_REGRESSION_SCRIPT'])\nspec = importlib.util.spec_from_file_location('runner', module_path)\nrunner = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(runner)\nPLAN = json.loads("+repr(json.dumps(plan))+ ")\n@pytest.mark.parametrize('case', PLAN['cases'])\ndef test_contract(case):\n    if case.get('kind') == 'exploratory': pytest.skip('Exploratory case has no exact oracle')\n    if os.environ.get('API_REGRESSION_APPROVED') != '1': pytest.skip('Explicit read-only approval required')\n    report = runner.execute({'cases':[case], 'skipped':[]}, os.environ['API_REGRESSION_BASE_URL'], True)\n    assert report['results'][0]['verdict'] == 'passed', report\n"
            Path(args.export_pytest).write_text(source,encoding='utf-8')
        report=execute(plan,args.base_url,args.approve_read_only,args.timeout) if args.base_url else plan
        print(json.dumps(report,ensure_ascii=False,indent=2))
        return 1 if any(r['verdict'] in ('failed','error') for r in report.get('results',[])) else 0
    except (ValueError,OSError,TypeError,KeyError,RecursionError) as exc:
        print(json.dumps({'error':str(exc)}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
