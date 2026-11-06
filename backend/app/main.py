from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from decimal import Decimal
import sys
from pathlib import Path

# Add project root to sys.path to access database/seed
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.api.routes import health, auth, karigars, transactions, inventory, transaction_details
from app.models.user import User, UserRole
from app.models.karigar import Karigar
from app.models.inventory import GoldInventory
from app.models.transaction import GoldTransaction, TransactionType
from app.core.security import get_password_hash
from app.services.gold_calculations import calculate_fine_gold
from database.seed.sample_data import (
    CLIENT_BRIEF_SPECIFICATIONS,
    SYNTHETIC_KARIGAR_PROFILES,
    SYNTHETIC_VAULT_INVENTORY
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_initial_data():
    """
    Seeds baseline demonstration data with clear taxonomy:
    1. Operational staff user accounts (Finance Head, Clerk, Manager, Craftsman).
    2. CLIENT_REFERENCE_PROFILES: 4 core master craftsmen from Coimbatore problem statement.
    3. ADDITIONAL_SYNTHETIC_KARIGARS: Additional craftsmen representing the 40 workshop artisans.
    4. CLIENT_REFERENCE_VAULT_INVENTORY: Bullion ingots, alloy casting grains, and scrap.
    """
    try:
        db = SessionLocal()
        try:
            if db.query(User).count() == 0:
                logger.info("Seeding demonstration user accounts...")
                
                # 1. Admin / Finance Head
                admin_user = User(
                    email="finance@karigarflow.com",
                    hashed_password=get_password_hash("Finance@123"),
                    full_name="K. Ramanathan (Finance Head)",
                    role=UserRole.ADMIN.value,
                    is_active=True
                )
                
                # 2. Issue Clerk
                clerk_user = User(
                    email="clerk@karigarflow.com",
                    hashed_password=get_password_hash("Clerk@123"),
                    full_name="M. Sundaram (Gold Issue Clerk)",
                    role=UserRole.ISSUE_CLERK.value,
                    is_active=True
                )

                # 3. Workshop Manager
                manager_user = User(
                    email="manager@karigarflow.com",
                    hashed_password=get_password_hash("Manager@123"),
                    full_name="S. Velumani (Workshop Master)",
                    role=UserRole.WORKSHOP_MANAGER.value,
                    is_active=True
                )

                # 4. Karigar Login User
                karigar_user = User(
                    email="karigar1@karigarflow.com",
                    hashed_password=get_password_hash("Karigar@123"),
                    full_name="Anand Swamy (Master Goldsmith)",
                    role=UserRole.KARIGAR.value,
                    is_active=True
                )

                db.add_all([admin_user, clerk_user, manager_user, karigar_user])
                db.commit()
                db.refresh(karigar_user)

                logger.info("Seeding SYNTHETIC_KARIGAR_PROFILES (representing Coimbatore workshop artisans)...")
                for idx, p in enumerate(SYNTHETIC_KARIGAR_PROFILES):
                    k = Karigar(
                        karigar_code=p["karigar_code"],
                        name=p["name"],
                        phone=p["phone"],
                        specialization=p["specialization"],
                        benchmark_wastage_percent=p["benchmark_wastage_percent"],
                        opening_balance_gross=p["opening_balance_gross"],
                        opening_balance_fine=p["opening_balance_fine"],
                        user_id=karigar_user.id if idx == 0 else None,
                        is_active=True
                    )
                    db.add(k)

                logger.info("Seeding SYNTHETIC_VAULT_INVENTORY (bullion, casting grains, scrap)...")
                for item in SYNTHETIC_VAULT_INVENTORY:
                    inv = GoldInventory(
                        lot_code=item["lot_code"],
                        category=item["category"],
                        description=item["description"],
                        gross_weight=item["gross_weight"],
                        purity_percent=item["purity_percent"],
                        fine_weight=item["fine_weight"],
                        location=item["location"]
                    )
                    db.add(inv)

                db.commit()
                logger.info("Successfully seeded KarigarFlow baseline data with clear reference/synthetic taxonomy!")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during schema/seed initialization: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing KarigarFlow backend database tables...")
    seed_initial_data()
    yield
    logger.info("KarigarFlow backend shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="KarigarFlow: Internal Jewellery Workshop Operations and Gold Inventory ERP",
    version="0.1.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(karigars.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(transaction_details.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": "KarigarFlow ERP",
        "description": "Internal Jewellery Workshop Operations & Gold Accounting",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }
