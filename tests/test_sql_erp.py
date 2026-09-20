import pytest
from sqlalchemy import func, select

from lastbuy.sql_erp import ERPBase, Requisition, SQLSyntheticERP


def test_independent_erp_restart_unique_key_and_payload_conflict(tmp_path):
    url = "sqlite:///" + str(tmp_path / "external.db")
    erp = SQLSyntheticERP(url)
    ERPBase.metadata.create_all(erp.store.engine)
    key = "a" * 64
    payload = {"synthetic": True, "quantity": 10000}
    with pytest.raises(TimeoutError):
        erp.create_draft(key, payload, lose_response=True)
    restarted = SQLSyntheticERP(url)
    assert restarted.create_draft(key, payload) == restarted.lookup(key)
    with pytest.raises(ValueError, match="conflicts"):
        restarted.create_draft(key, {**payload, "quantity": 11000})
    with restarted.store.session() as s:
        assert s.scalar(select(func.count()).select_from(Requisition)) == 1
    with pytest.raises(ValueError):
        restarted.create_draft("b" * 64, {"synthetic": False})
