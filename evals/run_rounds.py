"""Record three repeatable local test rounds; not an independent Agent evaluation."""
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
runs=[]
for index in range(3):
    run=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
    runs.append({'round':index+1,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr})
    if run.returncode:
        print(run.stderr)
        raise SystemExit(run.returncode)
report={'date':'2026-11-10','environment':sys.version,'rounds':runs,'limitation':'Repeated script tests, not independent Agent trials or exhaustive boundary coverage.'}
(root/'evals/results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('3 rounds passed')
