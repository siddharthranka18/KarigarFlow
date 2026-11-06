"""Run browser checks with a reset, isolated E2E DB and a managed API process."""
from pathlib import Path
import os
import socket
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
with socket.socket() as probe:
    if probe.connect_ex(('127.0.0.1', 8011)) == 0:
        raise RuntimeError('Port 8011 is already in use. Stop your E2E server before running this command.')
subprocess.run([sys.executable, str(root/'scripts/prepare_e2e.py'), '--reset'], check=True)
env = {**os.environ,
    'DATABASE_URL': os.environ.get('E2E_DATABASE_URL', 'postgresql+psycopg2://postgres@localhost:5433/karigarflow_e2e_db'),
    'FRONTEND_DIST': str(root/'frontend/dist'), 'SEED_DEMO_DATA': 'true', 'ENVIRONMENT': 'testing'}
if not (root/'frontend/dist/index.html').exists():
    raise RuntimeError('Run npm run build in frontend first')
(root/'artifacts').mkdir(exist_ok=True)
with (root/'artifacts/e2e-server.log').open('w', encoding='utf-8') as log:
    server = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--app-dir', str(root/'backend'),
        '--host', '127.0.0.1', '--port', '8011'], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    try:
        result = subprocess.run(['npx.cmd' if os.name == 'nt' else 'npx', 'playwright', 'test'], cwd=root/'frontend', check=False)
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()
sys.exit(result.returncode)
