import unittest, tempfile, os, subprocess
from pathlib import Path
from repro_capsule import env_snapshot, manifests, compare, capture

class T(unittest.TestCase):
    def test_redaction_manifest_compare(self):
        old=os.environ.get('DEMO_API_KEY'); os.environ['DEMO_API_KEY']='secret-value'
        try:
            self.assertEqual(env_snapshot(True)['DEMO_API_KEY'],'<redacted>')
        finally:
            if old is None: os.environ.pop('DEMO_API_KEY',None)
            else: os.environ['DEMO_API_KEY']=old
        d=Path(tempfile.mkdtemp()); (d/'pyproject.toml').write_text('[project]\nname="x"')
        self.assertIn('pyproject.toml',manifests(d))
        self.assertEqual(compare({'system':1},{'system':2})[0]['section'],'system')

    def test_manifest_symlink_outside_repo_is_skipped(self):
        d=Path(tempfile.mkdtemp())
        outside=Path(tempfile.mktemp())
        outside.write_text('outside dependency')
        (d/'requirements.txt').symlink_to(outside)
        self.assertNotIn('requirements.txt',manifests(d))

    def test_credential_bearing_urls_are_always_redacted(self):
        original={k:os.environ.get(k) for k in ('DATABASE_URL','REDIS_URL','PUBLIC_DOCS_URL','SERVICE_ENDPOINT')}
        os.environ['DATABASE_URL']='postgresql://alice:supersecret@db.example:5432/app'
        os.environ['REDIS_URL']='redis://:redispass@cache.example:6379/0'
        os.environ['PUBLIC_DOCS_URL']='https://docs.example/public'
        os.environ['SERVICE_ENDPOINT']='https://api.example/path?token=secret-query'
        try:
            snap=env_snapshot(True)
            self.assertEqual(snap['DATABASE_URL'],'<redacted>')
            self.assertEqual(snap['REDIS_URL'],'<redacted>')
            self.assertEqual(snap['SERVICE_ENDPOINT'],'<redacted>')
            self.assertEqual(snap['PUBLIC_DOCS_URL'],'https://docs.example/public')
        finally:
            for k,v in original.items():
                if v is None: os.environ.pop(k,None)
                else: os.environ[k]=v

    def test_capture_ignores_only_its_own_output_paths(self):
        d=Path(tempfile.mkdtemp())
        subprocess.run(['git','init','-q'],cwd=d,check=True)
        subprocess.run(['git','config','user.name','test'],cwd=d,check=True)
        subprocess.run(['git','config','user.email','test@example.invalid'],cwd=d,check=True)
        (d/'README.md').write_text('demo\n')
        subprocess.run(['git','add','README.md'],cwd=d,check=True)
        subprocess.run(['git','commit','-qm','init'],cwd=d,check=True)
        json_out=d/'repro-capsule.json'; html_out=d/'repro-capsule.html'
        json_out.write_text('{}'); html_out.write_text('<p>x</p>')
        clean=capture(d,False,[json_out,html_out])
        self.assertFalse(clean['git']['dirty'])
        (d/'real-untracked.txt').write_text('keep visible')
        dirty=capture(d,False,[json_out,html_out])
        self.assertTrue(dirty['git']['dirty'])
        preview='\n'.join(dirty['git']['status_preview'])
        self.assertIn('real-untracked.txt',preview)
        self.assertNotIn('repro-capsule.json',preview)
        self.assertNotIn('repro-capsule.html',preview)

    def test_missing_or_file_repo_root_is_rejected(self):
        base=Path(tempfile.mkdtemp())
        missing=base/'missing'
        with self.assertRaisesRegex(FileNotFoundError,'repo path not found'):
            capture(missing)
        file_root=base/'project.txt'; file_root.write_text('not a directory')
        with self.assertRaisesRegex(NotADirectoryError,'not a directory'):
            capture(file_root)

    def test_cli_missing_root_fails_before_writing_outputs(self):
        base=Path(tempfile.mkdtemp())
        missing=base/'missing'; json_out=base/'out.json'; html_out=base/'out.html'
        cp=subprocess.run([os.sys.executable,'repro_capsule.py','capture',str(missing),'--json',str(json_out),'--html',str(html_out)],text=True,capture_output=True)
        self.assertEqual(cp.returncode,2)
        self.assertIn('repo path not found',cp.stderr)
        self.assertFalse(json_out.exists()); self.assertFalse(html_out.exists())
