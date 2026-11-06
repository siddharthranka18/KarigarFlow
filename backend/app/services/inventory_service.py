"""
Inventory & Vault Custody Service for KarigarFlow Jewellery ERP.

Location Accounting Invariants:
1. Central Strongroom Vault:
   Closing Vault Fine = Opening Vault Fine - Fine Gold Issued + Fine Gold Physically Returned + Purchases Fine
   Closing Vault Gross = Opening Vault Gross - Gross Gold Issued + Gross Gold Physically Returned + Purchases Gross

2. Karigar Bench Custody:
   Closing Karigar Fine = Opening Karigar Fine + Fine Gold Issued - Fine Gold Physically Returned - Settled Wastage Fine - Loss Adjusted Fine
   Closing Karigar Gross = Opening Karigar Gross + Gross Gold Issued - Gross Gold Physically Returned - Settled Wastage Gross - Loss Adjusted Gross

3. Refinery Stock:
   Closing Refinery Fine = Opening Refinery Fine + Dispatches to Refinery Fine - Returns from Refinery Fine

4. Company-Wide Physical Gold Conservation:
   Total Physical Company Fine = Closing Vault Fine + Closing Refinery Fine + Closing Karigar Custody Fine
   Total Physical Company Fine == Opening Company Fine - Settled Wastage Fine - Loss Adjusted Fine + Purchases Fine
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple, List, Any
from sqlalchemy.orm import Session

from app.models.inventory import GoldInventory
from app.models.transaction import GoldTransaction, TransactionType
from app.models.karigar import Karigar
from app.services.gold_calculations import round_weight, ZERO_WEIGHT

class VaultCustodyPosition(NamedTuple):
    opening_central_vault_gross: Decimal
    opening_central_vault_fine: Decimal
    opening_refinery_gross: Decimal
    opening_refinery_fine: Decimal
    
    total_issued_gross: Decimal
    total_issued_fine: Decimal
    
    total_returned_ornament_gross: Decimal
    total_returned_ornament_fine: Decimal
    total_returned_scrap_gross: Decimal
    total_returned_scrap_fine: Decimal
    total_returned_dust_gross: Decimal
    total_returned_dust_fine: Decimal
    
    total_physically_returned_gross: Decimal
    total_physically_returned_fine: Decimal
    
    total_purchases_gross: Decimal
    total_purchases_fine: Decimal
    
    closing_central_vault_gross: Decimal
    closing_central_vault_fine: Decimal
    
    closing_refinery_gross: Decimal
    closing_refinery_fine: Decimal
    
    total_vault_and_refinery_fine: Decimal

def compute_vault_custody_position(
    db: Session,
    as_of_transaction_id: int = None
) -> VaultCustodyPosition:
    """
    Computes real-time Central Vault and Refinery custody balances based on the perpetual inventory invariant:
    Closing Vault Fine = Opening Vault Fine - Issued Fine + Physically Returned Fine + Purchases Fine
    """
    # 1. Opening baseline from inventory lots
    vault_items = db.query(GoldInventory).all()
    
    refiner_items = [
        item for item in vault_items 
        if "refin" in (item.category or "").lower() or "refin" in (item.location or "").lower()
    ]
    central_items = [item for item in vault_items if item not in refiner_items]

    open_refiner_gross = sum((Decimal(str(item.gross_weight)) for item in refiner_items), ZERO_WEIGHT)
    open_refiner_fine = sum((Decimal(str(item.fine_weight)) for item in refiner_items), ZERO_WEIGHT)
    open_central_gross = sum((Decimal(str(item.gross_weight)) for item in central_items), ZERO_WEIGHT)
    open_central_fine = sum((Decimal(str(item.fine_weight)) for item in central_items), ZERO_WEIGHT)

    # 2. Query transactions
    tx_query = db.query(GoldTransaction)
    if as_of_transaction_id is not None:
        tx_query = tx_query.filter(GoldTransaction.id <= as_of_transaction_id)
    all_txs = tx_query.all()

    # Movement categories
    issued_gross = ZERO_WEIGHT
    issued_fine = ZERO_WEIGHT
    
    ornament_gross = ZERO_WEIGHT
    ornament_fine = ZERO_WEIGHT
    
    scrap_gross = ZERO_WEIGHT
    scrap_fine = ZERO_WEIGHT
    
    dust_gross = ZERO_WEIGHT
    dust_fine = ZERO_WEIGHT
    
    purchases_gross = ZERO_WEIGHT
    purchases_fine = ZERO_WEIGHT

    for tx in all_txs:
        t_type = tx.transaction_type
        g = Decimal(str(tx.gross_weight or 0))
        f = Decimal(str(tx.fine_weight or 0))

        if t_type == TransactionType.ISSUE.value:
            issued_gross += g
            issued_fine += f
        elif t_type == TransactionType.RECEIPT_ORNAMENT.value:
            ornament_gross += g
            ornament_fine += f
        elif t_type == TransactionType.RECEIPT_SCRAP.value:
            scrap_gross += g
            scrap_fine += f
        elif t_type == TransactionType.RECEIPT_DUST.value:
            dust_gross += g
            dust_fine += f
        elif t_type == TransactionType.PURCHASE.value:
            purchases_gross += g
            purchases_fine += f

    phys_returned_gross = ornament_gross + scrap_gross + dust_gross
    phys_returned_fine = ornament_fine + scrap_fine + dust_fine

    # 3. Apply the vault perpetual inventory invariant
    closing_central_gross = open_central_gross - issued_gross + phys_returned_gross + purchases_gross
    closing_central_fine = open_central_fine - issued_fine + phys_returned_fine + purchases_fine

    closing_refiner_gross = open_refiner_gross
    closing_refiner_fine = open_refiner_fine

    total_vault_and_refinery_fine = closing_central_fine + closing_refiner_fine

    return VaultCustodyPosition(
        opening_central_vault_gross=round_weight(open_central_gross),
        opening_central_vault_fine=round_weight(open_central_fine),
        opening_refinery_gross=round_weight(open_refiner_gross),
        opening_refinery_fine=round_weight(open_refiner_fine),
        total_issued_gross=round_weight(issued_gross),
        total_issued_fine=round_weight(issued_fine),
        total_returned_ornament_gross=round_weight(ornament_gross),
        total_returned_ornament_fine=round_weight(ornament_fine),
        total_returned_scrap_gross=round_weight(scrap_gross),
        total_returned_scrap_fine=round_weight(scrap_fine),
        total_returned_dust_gross=round_weight(dust_gross),
        total_returned_dust_fine=round_weight(dust_fine),
        total_physically_returned_gross=round_weight(phys_returned_gross),
        total_physically_returned_fine=round_weight(phys_returned_fine),
        total_purchases_gross=round_weight(purchases_gross),
        total_purchases_fine=round_weight(purchases_fine),
        closing_central_vault_gross=round_weight(closing_central_gross),
        closing_central_vault_fine=round_weight(closing_central_fine),
        closing_refinery_gross=round_weight(closing_refiner_gross),
        closing_refinery_fine=round_weight(closing_refiner_fine),
        total_vault_and_refinery_fine=round_weight(total_vault_and_refinery_fine)
    )

