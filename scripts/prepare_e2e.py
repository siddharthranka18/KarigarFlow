"""Create/migrate a dedicated browser-test database; never reset the demo DB."""
import os
from pathlib import Path
import subprocess
import sys
import psycopg2
from urllib.parse import urlparse

url = os.environ.get('E2E_DATABASE_URL', 'postgresql+psycopg2://postgres@localhost:5433/karigarflow_e2e_db')
parsed = urlparse(url)
if parsed.path != '/karigarflow_e2e_db':
    raise RuntimeError('E2E database must be named karigarflow_e2e_db')
connection = psycopg2.connect(host=parsed.hostname, port=parsed.port or 5432,
    user=parsed.username, password=parsed.password or '', dbname='postgres')
connection.autocommit = True
with connection.cursor() as cursor:
    cursor.execute('SELECT 1 FROM pg_database WHERE datname=%s', ('karigarflow_e2e_db',))
    if cursor.fetchone() is None:
        cursor.execute('CREATE DATABASE karigarflow_e2e_db')
connection.close()
env = {**os.environ, 'DATABASE_URL': url}
subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'],
    cwd=Path(__file__).resolve().parents[1] / 'backend', env=env, check=True)
if '--reset' in sys.argv:
    # This destructive fixture reset is restricted to the named disposable DB.
    connection = psycopg2.connect(host=parsed.hostname, port=parsed.port or 5432,
        user=parsed.username, password=parsed.password or '', dbname='karigarflow_e2e_db')
    with connection:
        with connection.cursor() as cursor:
            cursor.execute('TRUNCATE TABLE scale_readings, gold_transactions, gold_inventory, karigars, users RESTART IDENTITY CASCADE')
    connection.close()
