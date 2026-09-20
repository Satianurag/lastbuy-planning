"""Initialize once; running again never replenishes the user's allowance."""

import os

from lastbuy.store import BudgetAccount, Store

store = Store(os.environ["LASTBUY_BUDGET_DATABASE_URL"])
with store.transaction() as session:
    account = session.get(BudgetAccount, "development")
    if account is None:
        account = BudgetAccount(
            id="development", limit_paise=70_000, reserved_paise=20_000
        )
        session.add(account)
    print(
        {
            "limit_paise": account.limit_paise,
            "reserved_paise": account.reserved_paise,
            "remaining_attempts": (account.limit_paise - account.reserved_paise)
            // 1000,
            "note": "Conservative admission allowance, not measured Azure charges",
        }
    )
