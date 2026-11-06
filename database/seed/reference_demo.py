"""Idempotent, additive demonstration seeding. Never clears existing ledgers."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from app.models.user import User
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction
from app.core.security import get_password_hash
from app.services.gold_calculations import calculate_fine_gold


def seed_reference_demo(db):
    owner = db.query(User).filter_by(email='owner@karigarflow.com').first()
    if not owner:
        db.add(User(email='owner@karigarflow.com', full_name='Demo Managing Partner', role='owner',
            hashed_password=get_password_hash('Owner@123'), is_active=True))
    finance = db.query(User).filter_by(email='finance@karigarflow.com').first()
    if finance and finance.role == 'admin':
        finance.role = 'finance_head'
    db.flush()
    reference_user = db.query(User).filter_by(email='murugesan@karigarflow.com').first()
    if not reference_user:
        reference_user = User(email='murugesan@karigarflow.com', full_name='Murugesan S (reference demo)',
            role='karigar', hashed_password=get_password_hash('Karigar@123'), is_active=True)
        db.add(reference_user)
        db.flush()
    karigar = db.query(Karigar).filter_by(karigar_code='KG-REFERENCE').first()
    if not karigar:
        karigar = Karigar(karigar_code='KG-REFERENCE', name='Murugesan S', specialization='Reference necklace sample',
            opening_balance_gross=0, opening_balance_fine=0, benchmark_wastage_percent=Decimal('3.00'),
            wastage_by_category={'necklace': '3.00', 'general': '3.00'}, is_active=True)
        db.add(karigar)
        db.flush()
    if karigar.user_id is None:
        karigar.user_id = reference_user.id
    for slip, kind, gross in [('TX-30411', 'ISSUE', '120.000'), ('TX-30437', 'RECEIPT_ORNAMENT', '112.450'), ('TX-30438', 'RECEIPT_SCRAP', '3.300')]:
        if db.query(GoldTransaction).filter_by(slip_number=slip).first():
            continue
        db.add(GoldTransaction(slip_number=slip, idempotency_key=f'demo:{slip}',
            transaction_type=kind, karigar_id=karigar.id, created_by_user_id=finance.id if finance else None,
            item_description='Client reference example — synthetic demo', job_number='JOB-30411', item_category='necklace',
            related_slip_number='TX-30411' if kind != 'ISSUE' else None,
            gross_weight=Decimal(gross), stone_weight=0, net_weight=Decimal(gross),
            purity_percent=Decimal('91.60'), fine_weight=calculate_fine_gold(gross, '91.60'),
            allowed_wastage_percent=Decimal('3.00'), actual_wastage_weight=0,
            scale_reading_confirmed=False, notes='Reference values from supplied brief; no wastage has been reported.'))
    # Separate, explicitly synthetic history to demonstrate early drift review.
    drift = db.query(Karigar).filter_by(karigar_code='KG-DRIFT').first()
    if not drift:
        drift = Karigar(karigar_code='KG-DRIFT', name='Demo drift review', specialization='Synthetic necklaces',
            opening_balance_gross=Decimal('100.000'), opening_balance_fine=Decimal('91.600'),
            benchmark_wastage_percent=Decimal('3.00'), wastage_by_category={'necklace': '3.00'}, is_active=True)
        db.add(drift)
        db.flush()
    for index, rate in enumerate(['0.10', '0.10', '0.10', '0.20', '0.20', '0.20']):
        slip = f'DEMO-DRIFT-{index}'
        if db.query(GoldTransaction).filter_by(slip_number=slip).first():
            continue
        db.add(GoldTransaction(slip_number=slip, transaction_type='RECEIPT_ORNAMENT', karigar_id=drift.id,
            item_description='Synthetic historical trend demo', job_number='OPENING', item_category='necklace',
            gross_weight=Decimal('10.000'), stone_weight=0, net_weight=Decimal('10.000'),
            purity_percent=Decimal('91.60'), fine_weight=Decimal('9.160'), allowed_wastage_percent=Decimal('3.00'),
            actual_wastage_weight=Decimal(rate), scale_reading_confirmed=False,
            created_at=(datetime.now(timezone.utc)-timedelta(days=7-index)).replace(tzinfo=None),
            notes='Synthetic reported wastage metadata for drift demonstration; not an approved settlement.'))
    db.commit()
