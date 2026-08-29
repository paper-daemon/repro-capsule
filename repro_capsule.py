#!/usr/bin/env python3
import argparse, json, os, platform, shutil, subprocess, hashlib, html
from pathlib import Path

SECRET_KEYS=('TOKEN','SECRET','PASSWORD','PASSWD','API_KEY','APIKEY','AUTH','COOKIE','CREDENTIAL')
MANIFEST_NAMES=('requirements.txt','requirements-dev.txt','pyproject.toml','poetry.lock','package.json','package-lock.json','pnpm-lock.yaml','yarn.lock','Dockerfile','.python-version')

def run(cmd,cwd=None):
    try:
        p=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,timeout=4)
        return {'ok':p.returncode==0,'out':(p.stdout or p.stderr).strip()[:1200]}
    except Exception as e:
        return {'ok':False,'out':str(e)}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def env_snapshot(include_values=False):
    out={}
    for k,v in sorted(os.environ.items()):
        secret=any(x in k.upper() for x in SECRET_KEYS)
        if secret:
            out[k]='<redacted>'
        elif include_values:
            out[k]=v[:300]
        else:
            out[k]='<present>'
    return out
def tool_versions():
    probes={
        'python':['python3','--version'],
        'git':['git','--version'],
        'node':['node','--version'],
        'npm':['npm','--version'],
        'docker':['docker','--version'],
    }
    return {k:run(v) for k,v in probes.items() if shutil.which(v[0])}

def git_snapshot(repo):
    repo=Path(repo)
    if not (repo/'.git').exists():
        return {'present':False}
    head=run(['git','rev-parse','HEAD'],repo)
    branch=run(['git','branch','--show-current'],repo)
    status=run(['git','status','--short'],repo)
    return {
        'present':True,
        'head':head['out'],
        'branch':branch['out'],
        'dirty':bool(status['out']),
        'status_preview':status['out'].splitlines()[:30],
    }

def manifests(repo):
    repo=Path(repo); out={}
    for name in MANIFEST_NAMES:
        p=repo/name
        if p.exists() and p.is_file():
            out[name]={'sha256':sha(p),'size':p.stat().st_size}
    return out
def capture(repo='.', include_env_values=False):
    return {
        'system':{
            'platform':platform.platform(),
            'machine':platform.machine(),
            'python':platform.python_version(),
            'executable':os.sys.executable,
        },
        'tools':tool_versions(),
        'git':git_snapshot(repo),
        'manifests':manifests(repo),
        'environment':env_snapshot(include_env_values),
    }

def compare(a,b):
    out=[]
    for section in ('system','tools','git','manifests','environment'):
        if a.get(section)!=b.get(section):
            out.append({'section':section,'changed':True})
    return out

def render(data, drift=None):
    rows=''.join(
        f"<tr><td>{html.escape(k)}</td><td><pre>{html.escape(json.dumps(v,ensure_ascii=False,indent=2)[:5000])}</pre></td></tr>"
        for k,v in data.items()
    )
    drift_html=''
    if drift is not None:
        drift_html='<p>changed sections: '+', '.join(x['section'] for x in drift)+'</p>'
    return (
        '<!doctype html><meta charset="utf-8"><style>body{font:15px system-ui;max-width:1100px;margin:auto;padding:40px;background:#eee7dd}'
        'table{width:100%;border-collapse:collapse;background:#fffaf2}td{padding:10px;border-bottom:1px solid #ddd;vertical-align:top}'
        'pre{white-space:pre-wrap;margin:0}</style><h1>Repro Capsule</h1>'+drift_html+'<table>'+rows+'</table>'
    )
def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('capture'); c.add_argument('repo',nargs='?',default='.'); c.add_argument('--json',default='repro-capsule.json'); c.add_argument('--html',default='repro-capsule.html'); c.add_argument('--include-env-values',action='store_true')
    d=sub.add_parser('compare'); d.add_argument('before'); d.add_argument('after'); d.add_argument('--html',default='repro-drift.html')
    a=ap.parse_args()
    if a.cmd=='capture':
        data=capture(a.repo,a.include_env_values)
        Path(a.json).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        Path(a.html).write_text(render(data),encoding='utf-8')
        print(f"branch={data['git'].get('branch','-')} dirty={data['git'].get('dirty','-')} manifests={len(data['manifests'])}")
    else:
        before=json.loads(Path(a.before).read_text(encoding='utf-8')); after=json.loads(Path(a.after).read_text(encoding='utf-8'))
        drift=compare(before,after); Path(a.html).write_text(render(after,drift),encoding='utf-8'); print(f'drift_sections={len(drift)}')
if __name__=='__main__': main()
