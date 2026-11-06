from sqlalchemy.orm import aliased
from sqlalchemy import exists
from app.models.transaction import GoldTransaction


def unresolved_loss_conditions():
    adjustment = aliased(GoldTransaction)
    # Correlate on both slip and craftsman, never on free-text descriptions.
    resolved = exists().where(
        adjustment.transaction_type == 'LOSS_ADJUSTMENT',
        adjustment.related_slip_number == GoldTransaction.slip_number,
        adjustment.karigar_id == GoldTransaction.karigar_id,
    )
    return (
        GoldTransaction.transaction_type == 'RECEIPT_ORNAMENT',
        GoldTransaction.is_loss_alert.is_(True),
        ~resolved,
    )
