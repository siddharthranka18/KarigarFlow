from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from decimal import Decimal

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.api.routes import health, auth, karigars, transactions, inventory
from app.models.user import User, UserRole
from app.models.karigar import Karigar
from app.models.inventory import GoldInventory
from app.core.security import get_password_hash
from app.services.gold_calculations import calculate_fine_gold

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_initial_data():
    """Seeds baseline accounts and Coimbatore workshop demonstration data if not already present."""
    try:
        db = SessionLocal()
        try:
            # Check if users already seeded
            if db.query(User).count() == 0:
                logger.info("Seeding demonstration accounts...")
                
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

                # Seed Karigars representing the Coimbatore workshop
                sample_karigars = [
                    Karigar(
                        karigar_code="KG-CBE-001",
                        name="Anand Swamy",
                        phone="+91 98421 11201",
                        specialization="Temple Jewellery & Chains",
                        benchmark_wastage_percent=Decimal("2.20"),
                        opening_balance_gross=Decimal("45.250"),
                        opening_balance_fine=Decimal("41.449"),
                        user_id=karigar_user.id
                    ),
                    Karigar(
                        karigar_code="KG-CBE-002",
                        name="P. Murugesan",
                        phone="+91 98421 11202",
                        specialization="Solid Bangles & Kadas",
                        benchmark_wastage_percent=Decimal("1.80"),
                        opening_balance_gross=Decimal("82.100"),
                        opening_balance_fine=Decimal("75.204")
                    ),
                    Karigar(
                        karigar_code="KG-CBE-003",
                        name="D. Rajesh",
                        phone="+91 98421 11203",
                        specialization="Antique Choker & Casting",
                        benchmark_wastage_percent=Decimal("2.50"),
                        opening_balance_gross=Decimal("110.000"),
                        opening_balance_fine=Decimal("100.760")
                    ),
                    Karigar(
                        karigar_code="KG-CBE-004",
                        name="G. Selvam",
                        phone="+91 98421 11204",
                        specialization="Stone Setting & Navratna",
                        benchmark_wastage_percent=Decimal("2.00"),
                        opening_balance_gross=Decimal("30.500"),
                        opening_balance_fine=Decimal("27.938")
                    )
                ]
                db.add_all(sample_karigars)

                # Seed Workshop Vault Inventory
                sample_inventory = [
                    GoldInventory(
                        lot_code="LOT-2026-RAW-01",
                        category="24K Bullion Bar (999.0)",
                        description="MMTC-PAMP 1000g Bullion Bar #A4892",
                        gross_weight=Decimal("1000.000"),
                        purity_percent=Decimal("99.90"),
                        fine_weight=Decimal("999.000"),
                        location="Coimbatore Central Strongroom Vault"
                    ),
                    GoldInventory(
                        lot_code="LOT-2026-GRAIN-22K",
                        category="22K Alloy Grains (916)",
                        description="Workshop Ready Cast Grains 91.60% Hallmarked",
                        gross_weight=Decimal("450.000"),
                        purity_percent=Decimal("91.60"),
                        fine_weight=calculate_fine_gold(Decimal("450.000"), Decimal("91.60")),
                        location="Workshop Floor Dispense Safe #2"
                    ),
                    GoldInventory(
                        lot_code="LOT-2026-SCRAP-MELT",
                        category="Scrap for Refining",
                        description="Recovered cuttings, wire ends, and old gold exchange scrap",
                        gross_weight=Decimal("128.450"),
                        purity_percent=Decimal("88.50"),
                        fine_weight=calculate_fine_gold(Decimal("128.450"), Decimal("88.50")),
                        location="Refinery Dispatch Tray"
                    )
                ]
                db.add_all(sample_inventory)
                db.commit()
                logger.info("Successfully seeded KarigarFlow baseline data!")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during schema/seed initialization: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Initializing KarigarFlow backend database tables...")
    seed_initial_data()
    yield
    # Shutdown actions
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
app.include_router(inventory.router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": "KarigarFlow ERP",
        "description": "Internal Jewellery Workshop Operations & Gold Accounting",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }

