from app.schemas.transaction import TransactionResponse


def visible_transaction(tx, user):
    result = TransactionResponse.model_validate(tx)
    if user.role not in {'admin', 'owner', 'finance_head'}:
        result.is_loss_alert = False
        if result.transaction_type == 'LOSS_ADJUSTMENT':
            result.notes = 'Finance-approved accounting adjustment. Contact Finance for review details.'
    return result
