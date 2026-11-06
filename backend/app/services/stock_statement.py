"""Date-based custody reconstruction from opening stock and persisted ledger entries."""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.inventory import GoldInventory
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction
from app.schemas.stock_statement import StockRow, StockStatement
from app.services.gold_calculations import round_weight

# India has no daylight saving time; a fixed offset also works without OS tzdata.
WORKSHOP_TZ = timezone(timedelta(hours=5, minutes=30))
LOCATIONS = ('Central vault', 'Refinery', 'Karigar custody')
MOVEMENTS = ('issues', 'receipts', 'purchases', 'wastage', 'loss_adjustments')
ZERO = Decimal('0.000')


def build_stock_statement(db: Session, statement_date: date) -> StockStatement:
    start = datetime.combine(statement_date, time.min, tzinfo=WORKSHOP_TZ).astimezone(timezone.utc)
    end = start + timedelta(days=1)
    # Opening lots/profiles are treated as the baseline preceding ledger history.
    inventory = db.query(GoldInventory).all()
    karigars = db.query(Karigar).all()
    # The existing schema stores naive UTC, so never send an aware SQL boundary:
    # PostgreSQL would otherwise convert it using the session timezone.
    transactions = db.query(GoldTransaction).filter(
        GoldTransaction.created_at < end.replace(tzinfo=None)
    ).all()
    opening = {(loc, unit): ZERO for loc in LOCATIONS for unit in ('gross', 'fine')}
    movements = {key: {name: ZERO for name in MOVEMENTS} for key in opening}

    for item in inventory:
        location = 'Refinery' if 'refin' in f'{item.category} {item.location}'.lower() else 'Central vault'
        for unit in ('gross', 'fine'):
            opening[location, unit] += Decimal(str(getattr(item, f'{unit}_weight')))
    # Inactive karigars can still hold gold and must remain in custody totals.
    for karigar in karigars:
        for unit in ('gross', 'fine'):
            opening['Karigar custody', unit] += Decimal(str(getattr(karigar, f'opening_balance_{unit}') or 0))

    count = 0
    for tx in transactions:
        recorded = tx.created_at
        if recorded.tzinfo is None:
            recorded = recorded.replace(tzinfo=timezone.utc)
        in_day = recorded >= start
        if in_day:
            count += 1
        effects = {
            'ISSUE': (('Central vault', 'issues', -1), ('Karigar custody', 'issues', 1)),
            'RECEIPT_ORNAMENT': (('Central vault', 'receipts', 1), ('Karigar custody', 'receipts', -1)),
            'RECEIPT_SCRAP': (('Central vault', 'receipts', 1), ('Karigar custody', 'receipts', -1)),
            'RECEIPT_DUST': (('Central vault', 'receipts', 1), ('Karigar custody', 'receipts', -1)),
            'PURCHASE': (('Central vault', 'purchases', 1),),
            'WASTAGE_SETTLEMENT': (('Karigar custody', 'wastage', -1),),
            'LOSS_ADJUSTMENT': (('Karigar custody', 'loss_adjustments', -1),),
        }.get(tx.transaction_type, ())
        for location, name, sign in effects:
            for unit in ('gross', 'fine'):
                value = Decimal(str(getattr(tx, f'{unit}_weight'))) * sign
                if in_day:
                    movements[location, unit][name] += value
                else:
                    opening[location, unit] += value

    rows = []
    for location in LOCATIONS:
        for unit in ('gross', 'fine'):
            key = (location, unit)
            values = movements[key]
            rows.append(StockRow(location=location, unit=unit,
                opening=round_weight(opening[key]),
                **{name: round_weight(value) for name, value in values.items()},
                closing=round_weight(opening[key] + sum(values.values(), ZERO))))
    for unit in ('gross', 'fine'):
        matching = [row for row in rows if row.unit == unit]
        fields = ('opening', *MOVEMENTS, 'closing')
        rows.append(StockRow(location='Company total', unit=unit,
            **{name: round_weight(sum((getattr(row, name) for row in matching), ZERO)) for name in fields}))
    return StockStatement(date=statement_date, transaction_count=count, rows=rows)
