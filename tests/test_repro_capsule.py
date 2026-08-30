import unittest, tempfile, os
from pathlib import Path
from repro_capsule import env_snapshot, manifests, compare

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
