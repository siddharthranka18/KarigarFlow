"""
Pytest configuration and database isolation fixtures for KarigarFlow.

CRITICAL SAFETY RULES:
1. Automated tests must NEVER mutate karigarflow_db (the development/demo database).
2. Tests exclusively target karigarflow_test_db.
3. Database state is reset deterministically before each test.
4. Running pytest repeatedly must cause zero row changes in karigarflow_db.
"""

import os
import pytest
from decimal import Decimal
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 1. Enforce test database URL before importing any app modules
TEST_DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5433/karigarflow_test_db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "testing"

# Safety verification
from urllib.parse import urlparse
db_name = urlparse(TEST_DATABASE_URL).path.lstrip("/")
assert db_name == "karigarflow_test_db", "FATAL: Test suite must only point to karigarflow_test_db!"

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.karigar import Karigar
from app.models.inventory import GoldInventory
from app.models.transaction import GoldTransaction
from app.core.security import get_password_hash, create_access_token
from fastapi.testclient import TestClient

# Create dedicated test engine pointing exclusively to karigarflow_test_db
test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Dependency override ensuring all test requests use karigarflow_test_db."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override dependency globally on the FastAPI application
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database_schema():
    """Ensures test database has all tables created."""
    assert test_engine.url.database == "karigarflow_test_db"
    Base.metadata.create_all(bind=test_engine)
    yield

@pytest.fixture(autouse=True)
def isolate_and_seed_test_db():
    """
    Autouse fixture that runs before each test:
    - Truncates tables in karigarflow_test_db
    - Seeds clean, deterministic baseline data
    - Leaves karigarflow_db completely untouched
    """
    assert test_engine.url.database == "karigarflow_test_db"
    db = TestingSessionLocal()
    try:
        # 1. Truncate test tables
        db.execute(text("TRUNCATE TABLE gold_transactions RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE gold_inventory RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE karigars RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE;"))
        db.commit()

        # 2. Seed deterministic users
        admin_user = User(
            id=1,
            email="finance@karigarflow.com",
            hashed_password=get_password_hash("Finance@123"),
            full_name="K. Ramanathan (Finance Head)",
            role=UserRole.ADMIN.value,
            is_active=True
        )
        clerk_user = User(
            id=2,
            email="clerk@karigarflow.com",
            hashed_password=get_password_hash("Clerk@123"),
            full_name="M. Sundaram (Gold Issue Clerk)",
            role=UserRole.ISSUE_CLERK.value,
            is_active=True
        )
        manager_user = User(
            id=3,
            email="manager@karigarflow.com",
            hashed_password=get_password_hash("Manager@123"),
            full_name="S. Velumani (Workshop Master)",
            role=UserRole.WORKSHOP_MANAGER.value,
            is_active=True
        )
        karigar_user = User(
            id=4,
            email="karigar1@karigarflow.com",
            hashed_password=get_password_hash("Karigar@123"),
            full_name="Anand Swamy (Master Goldsmith)",
            role=UserRole.KARIGAR.value,
            is_active=True
        )
        db.add_all([admin_user, clerk_user, manager_user, karigar_user])
        db.commit()

        # 3. Seed deterministic karigars (Core 4 craftsmen from problem statement)
        k1 = Karigar(
            id=1,
            karigar_code="KG-CBE-001",
            name="Anand Swamy",
            phone="+91 98421 11201",
            specialization="Temple Jewellery & Handcrafted Chains",
            benchmark_wastage_percent=Decimal("2.20"),
            opening_balance_gross=Decimal("45.250"),
            opening_balance_fine=Decimal("41.449"),
            user_id=4,
            is_active=True
        )
        k2 = Karigar(
            id=2,
            karigar_code="KG-CBE-002",
            name="P. Murugesan",
            phone="+91 98421 11202",
            specialization="Solid Bangles & Kadas",
            benchmark_wastage_percent=Decimal("1.80"),
            opening_balance_gross=Decimal("82.100"),
            opening_balance_fine=Decimal("75.204"),
            is_active=True
        )
        k3 = Karigar(
            id=3,
            karigar_code="KG-CBE-003",
            name="D. Rajesh",
            phone="+91 98421 11203",
            specialization="Antique Choker & Centrifugal Casting",
            benchmark_wastage_percent=Decimal("2.50"),
            opening_balance_gross=Decimal("110.000"),
            opening_balance_fine=Decimal("100.760"),
            is_active=True
        )
        k4 = Karigar(
            id=4,
            karigar_code="KG-CBE-004",
            name="G. Selvam",
            phone="+91 98421 11204",
            specialization="Stone Setting & Navratna Work",
            benchmark_wastage_percent=Decimal("2.00"),
            opening_balance_gross=Decimal("30.500"),
            opening_balance_fine=Decimal("27.938"),
            is_active=True
        )
        db.add_all([k1, k2, k3, k4])
        db.commit()

        # 4. Seed deterministic vault inventory
        lot1 = GoldInventory(
            id=1,
            lot_code="LOT-2026-RAW-01",
            category="24K Bullion Bar (999.0)",
            description="MMTC-PAMP 1000g Bullion Bar #A4892",
            gross_weight=Decimal("1000.000"),
            purity_percent=Decimal("99.90"),
            fine_weight=Decimal("999.000"),
            location="Coimbatore Central Strongroom Vault"
        )
        lot2 = GoldInventory(
            id=2,
            lot_code="LOT-2026-GRAIN-22K",
            category="22K Alloy Grains (916)",
            description="Workshop Ready Cast Grains 91.60% Hallmarked",
            gross_weight=Decimal("450.000"),
            purity_percent=Decimal("91.60"),
            fine_weight=Decimal("412.200"),
            location="Workshop Floor Dispense Safe #2"
        )
        lot3 = GoldInventory(
            id=3,
            lot_code="LOT-2026-SCRAP-MELT",
            category="Scrap for Refining",
            description="Recovered cuttings, wire ends, and old gold exchange scrap",
            gross_weight=Decimal("128.450"),
            purity_percent=Decimal("88.50"),
            fine_weight=Decimal("113.678"),
            location="Refinery Dispatch Tray"
        )
        db.add_all([lot1, lot2, lot3])
        db.commit()

        yield db
    finally:
        db.close()

@pytest.fixture
def test_db():
    """Provides a direct database session to karigarflow_test_db."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client():
    """FastAPI TestClient bound to test database."""
    return TestClient(app)

@pytest.fixture
def finance_token():
    return create_access_token({"sub": "finance@karigarflow.com", "role": "admin", "user_id": 1})

@pytest.fixture
def clerk_token():
    return create_access_token({"sub": "clerk@karigarflow.com", "role": "issue_clerk", "user_id": 2})

@pytest.fixture
def karigar_token():
    return create_access_token({"sub": "karigar1@karigarflow.com", "role": "karigar", "user_id": 4})

