"""Conservative development admission allowance, not an Azure billing hard cap."""

import os
import uuid

from sqlalchemy import update

from .domain import now
from .store import BudgetAccount, BudgetAttempt, Store


class BudgetExceeded(RuntimeError):
    pass


class BudgetGuard:
    def __init__(self, store=None):
        url = os.getenv("LASTBUY_BUDGET_DATABASE_URL")
        if store is None and not url:
            raise BudgetExceeded(
                "A shared development budget ledger must be configured"
            )
        self.store = store or Store(url, initialize=False)

    def ensure_run_allowance(self, attempts=4):
        with self.store.session() as session:
            account = session.get(BudgetAccount, "development")
            if (
                account is None
                or account.limit_paise - account.reserved_paise < attempts * 1000
            ):
                raise BudgetExceeded(
                    "Insufficient remaining development allowance for a complete analysis; no model call started"
                )

    def reserve(self, case_id, role):
        attempt_id = str(uuid.uuid4())
        allowance = 1000  # INR 10 per specialist attempt; retained on failure/retry.
        with self.store.transaction() as session:
            changed = session.execute(
                update(BudgetAccount)
                .where(
                    BudgetAccount.id == "development",
                    BudgetAccount.reserved_paise + allowance
                    <= BudgetAccount.limit_paise,
                )
                .values(reserved_paise=BudgetAccount.reserved_paise + allowance)
            )
            if changed.rowcount != 1:
                raise BudgetExceeded(
                    "Development analysis allowance exhausted or not initialized"
                )
            session.add(
                BudgetAttempt(
                    id=attempt_id,
                    account="development",
                    data={
                        "case_id": case_id,
                        "role": role,
                        "allowance_paise": allowance,
                        "at": now().isoformat(),
                        "status": "RESERVED",
                        "actual_bill": "unknown",
                    },
                )
            )
        return attempt_id

    def finish(self, attempt_id, result=None):
        with self.store.transaction() as session:
            attempt = session.get(BudgetAttempt, attempt_id)
            attempt.data = {
                **attempt.data,
                "status": "COMPLETE" if result else "FAILED_OR_UNCERTAIN",
                "usage": result.get("usage", {}) if result else {},
            }
