"""Bounded retries while establishing a SQL connection; never replays a write."""

import logging
import time

LOG = logging.getLogger("lastbuy.sql")


def connect_with_retry(dbapi, args, kwargs):
    for attempt in range(2):
        try:
            return dbapi.connect(*args, **kwargs)
        except dbapi.Error as error:
            state = str(error.args[0]) if error.args else ""
            transient = state in {"HYT00", "HYT01", "08S01"} or any(
                code in str(error)
                for code in ("40613", "40197", "40501", "49918", "49919", "49920")
            )
            if attempt or not transient:
                raise
            LOG.warning("sql_connect_retry state=%s attempt=2", state)
            time.sleep(1)
