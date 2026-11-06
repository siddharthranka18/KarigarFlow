from collections import defaultdict
from decimal import Decimal
from app.models.transaction import GoldTransaction
from app.services.gold_calculations import round_purity


def loss_drift_reviews(db):
    groups = defaultdict(list)
    rows = db.query(GoldTransaction).filter(GoldTransaction.transaction_type == 'RECEIPT_ORNAMENT').order_by(GoldTransaction.created_at.desc(), GoldTransaction.id.desc()).all()
    for tx in rows:
        if tx.karigar_id and tx.gross_weight > 0:
            groups[tx.karigar_id, tx.item_category or 'general'].append(tx)
    result = []
    for (karigar_id, category), history in groups.items():
        if len(history) < 6:
            continue
        def rate(batch):
            return sum((Decimal(str(t.actual_wastage_weight)) for t in batch), Decimal(0)) * 100 / sum((Decimal(str(t.gross_weight)) for t in batch), Decimal(0))
        recent, baseline = rate(history[:3]), rate(history[3:6])
        if recent - baseline >= Decimal('0.50'):
            result.append(dict(karigar_id=karigar_id, karigar_name=history[0].karigar_name,
                item_category=category, recent_percent=str(round_purity(recent)), baseline_percent=str(round_purity(baseline)),
                increase_points=str(round_purity(recent-baseline)), sample_count=6,
                slip_ids=[tx.id for tx in history[:6]], message='Reported wastage is rising. Review job conditions and measurements; this is not a finding of misconduct.'))
    return result
