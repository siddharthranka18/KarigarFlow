import pytest
from sqlalchemy import create_engine
from alembic.config import Config
from app.core.config import Settings


@pytest.mark.parametrize('scheme', ['postgresql://', 'postgres://', 'postgresql+psycopg2://'])
def test_hosted_connection_selects_installed_driver_and_preserves_encoding(scheme):
    # Synthetic URL only; never connect to this host or log a real credential.
    supplied = scheme + 'demo:sample%25value@database.example:5432/workshop?sslmode=require'
    settings = Settings(_env_file=None, DATABASE_URL=supplied)
    assert settings.DATABASE_URL == 'postgresql+psycopg2://demo:sample%25value@database.example:5432/workshop?sslmode=require'
    engine = create_engine(settings.DATABASE_URL)
    try:
        assert engine.dialect.driver == 'psycopg2'
        assert engine.url.password == 'sample%value'
        assert engine.url.query['sslmode'] == 'require'
        config = Config()
        config.set_main_option('sqlalchemy.url', settings.DATABASE_URL.replace('%', '%%'))
        assert config.get_main_option('sqlalchemy.url') == settings.DATABASE_URL
    finally:
        engine.dispose()
