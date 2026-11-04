"""
KarigarFlow Seed & Demonstration Data Reference.

DATA TAXONOMY CLARIFICATION (AUDIT COMPLIANT):
1. CLIENT_BRIEF_SPECIFICATIONS:
   Parameters explicitly stipulated in the client problem statement:
   - Location: Coimbatore internal workshop with 5 regional retail showrooms.
   - Scale: Approximately 40 karigars (goldsmiths) and ~180 employees.
   - Operating Model: Replaces paper ledger books (Vellai Thaal) and manual Excel sheets.
   - Standards: All gold weights stored to 3 decimal places (0.001g precision).
   - Purity: Stored to 2 decimal places (0.01% precision).
   - Scale Readings: Scale photos require mandatory human confirmation before ledger posting.
   - Explicit brief requirement: Application uses synthetic demonstration data.

2. SYNTHETIC_KARIGAR_PROFILES (Created for demonstration):
   Representative craftsmen profiles reflecting typical Coimbatore jewellery specializations
   (Temple jewellery, solid kadas, antique cast chokers, stone setting, die stamping, chains).
   All individual names, phone numbers, and opening balances are synthetic demonstration data.

3. SYNTHETIC_VAULT_INVENTORY (Created for demonstration):
   Synthetic vault holdings illustrating standard workshop raw materials
   (24K pure bullion bar, 22K 916 casting grain, and melting scrap).

4. SYNTHETIC_DEMO_TRANSACTIONS (Created for demonstration):
   Synthetic operational transactions exercising the complete lifecycle:
   Issue -> Jewellery Receipt -> Scrap Return -> Wastage Settlement -> Loss Alert.
"""

from decimal import Decimal

CLIENT_BRIEF_SPECIFICATIONS = {
    "location": "Coimbatore Internal Workshop, Tamil Nadu",
    "showroom_count": 5,
    "approximate_karigars": 40,
    "approximate_employees": 180,
    "weight_precision_decimals": 3,
    "purity_precision_decimals": 2,
    "scale_reading_human_confirmation_required": True,
    "uses_synthetic_demo_data": True
}

# Synthetic karigar profiles representing the ~40 workshop craftsmen
SYNTHETIC_KARIGAR_PROFILES = [
    {
        "karigar_code": "KG-CBE-001",
        "name": "Anand Swamy",
        "phone": "+91 98421 11201",
        "specialization": "Temple Jewellery & Handcrafted Chains",
        "benchmark_wastage_percent": Decimal("2.20"),
        "opening_balance_gross": Decimal("45.250"),
        "opening_balance_fine": Decimal("41.449"),  # 45.250g @ 91.60% purity
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-002",
        "name": "P. Murugesan",
        "phone": "+91 98421 11202",
        "specialization": "Solid Bangles & Kadas",
        "benchmark_wastage_percent": Decimal("1.80"),
        "opening_balance_gross": Decimal("82.100"),
        "opening_balance_fine": Decimal("75.204"),  # 82.100g @ 91.60% purity
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-003",
        "name": "D. Rajesh",
        "phone": "+91 98421 11203",
        "specialization": "Antique Choker & Centrifugal Casting",
        "benchmark_wastage_percent": Decimal("2.50"),
        "opening_balance_gross": Decimal("110.000"),
        "opening_balance_fine": Decimal("100.760"),  # 110.000g @ 91.60% purity
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-004",
        "name": "G. Selvam",
        "phone": "+91 98421 11204",
        "specialization": "Stone Setting & Navratna Work",
        "benchmark_wastage_percent": Decimal("2.00"),
        "opening_balance_gross": Decimal("30.500"),
        "opening_balance_fine": Decimal("27.938"),  # 30.500g @ 91.60% purity
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-005",
        "name": "K. Balan",
        "phone": "+91 98421 11205",
        "specialization": "Die Stamping & Medallions",
        "benchmark_wastage_percent": Decimal("1.50"),
        "opening_balance_gross": Decimal("25.000"),
        "opening_balance_fine": Decimal("22.900"),
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-006",
        "name": "M. Shanmugam",
        "phone": "+91 98421 11206",
        "specialization": "Handmade Hollow Rope Chains",
        "benchmark_wastage_percent": Decimal("2.20"),
        "opening_balance_gross": Decimal("60.000"),
        "opening_balance_fine": Decimal("54.960"),
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-007",
        "name": "V. Palanisamy",
        "phone": "+91 98421 11207",
        "specialization": "Centrifugal Casting & Pre-Polish",
        "benchmark_wastage_percent": Decimal("2.00"),
        "opening_balance_gross": Decimal("40.000"),
        "opening_balance_fine": Decimal("36.640"),
        "classification": "SYNTHETIC_DEMO_PROFILE"
    },
    {
        "karigar_code": "KG-CBE-008",
        "name": "R. Chandran",
        "phone": "+91 98421 11208",
        "specialization": "Micro-Prong Gem & Diamond Setting",
        "benchmark_wastage_percent": Decimal("1.80"),
        "opening_balance_gross": Decimal("18.500"),
        "opening_balance_fine": Decimal("16.946"),
        "classification": "SYNTHETIC_DEMO_PROFILE"
    }
]

# Synthetic central vault inventory lots
SYNTHETIC_VAULT_INVENTORY = [
    {
        "lot_code": "LOT-2026-RAW-01",
        "category": "24K Bullion Bar (999.0)",
        "description": "MMTC-PAMP 1000g Bullion Bar #A4892",
        "gross_weight": Decimal("1000.000"),
        "purity_percent": Decimal("99.90"),
        "fine_weight": Decimal("999.000"),
        "location": "Coimbatore Central Strongroom Vault",
        "classification": "SYNTHETIC_DEMO_INVENTORY"
    },
    {
        "lot_code": "LOT-2026-GRAIN-22K",
        "category": "22K Alloy Grains (916)",
        "description": "Workshop Ready Cast Grains 91.60% Hallmarked",
        "gross_weight": Decimal("450.000"),
        "purity_percent": Decimal("91.60"),
        "fine_weight": Decimal("412.200"),
        "location": "Workshop Floor Dispense Safe #2",
        "classification": "SYNTHETIC_DEMO_INVENTORY"
    },
    {
        "lot_code": "LOT-2026-SCRAP-MELT",
        "category": "Scrap for Refining",
        "description": "Recovered cuttings, wire ends, and old gold exchange scrap",
        "gross_weight": Decimal("128.450"),
        "purity_percent": Decimal("88.50"),
        "fine_weight": Decimal("113.678"),
        "location": "Refinery Dispatch Tray",
        "classification": "SYNTHETIC_DEMO_INVENTORY"
    }
]
