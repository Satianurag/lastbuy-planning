from concurrent.futures import ThreadPoolExecutor

import pytest

from lastbuy.budget import BudgetExceeded, BudgetGuard
from lastbuy.store import BudgetAccount, Store


def test_concurrent_attempts_cannot_overspend_allowance(tmp_path):
    store = Store("sqlite:///" + str(tmp_path / "budget.db"))
    with store.transaction() as session:
        session.add(
            BudgetAccount(id="development", limit_paise=3000, reserved_paise=2000)
        )
    guard = BudgetGuard(store)

    def reserve(_):
        try:
            return guard.reserve("CASE", "engineering")
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(reserve, range(4)))
    assert len([r for r in results if r]) == 1
    attempt = next(r for r in results if r)
    guard.finish(
        attempt
    )  # Failed/uncertain requests do not refund potentially billed usage.
    with pytest.raises(BudgetExceeded):
        guard.reserve("CASE", "service")


def test_missing_ledger_fails_closed(tmp_path):
    with pytest.raises(BudgetExceeded):
        BudgetGuard(Store("sqlite:///" + str(tmp_path / "empty.db"))).reserve(
            "CASE", "service"
        )


def test_partial_run_cannot_start_when_full_run_allowance_is_missing(tmp_path):
    from lastbuy.budget import BudgetExceeded, BudgetGuard
    from lastbuy.store import BudgetAccount, Store

    store = Store("sqlite:///" + str(tmp_path / "preflight.db"))
    with store.transaction() as session:
        session.add(
            BudgetAccount(id="development", limit_paise=70000, reserved_paise=67000)
        )
    guard = BudgetGuard(store)
    with pytest.raises(BudgetExceeded, match="complete analysis"):
        guard.ensure_run_allowance()
    with store.session() as session:
        assert session.get(BudgetAccount, "development").reserved_paise == 67000
