"""Server-only dispatch; ambiguous delivery remains a reconcilable durable outbox."""

import os
from urllib.parse import urlparse

import httpx


def dispatch_remote(job):
    if job.get("receipt"):
        return {**job, "status": "COMPLETE"}
    endpoint = os.environ["LASTBUY_EXPORT_URL"].rstrip("/")
    if urlparse(endpoint).scheme != "https":
        raise ValueError("Export transport requires HTTPS")
    try:
        response = httpx.post(
            endpoint + "/" + job["key"],
            headers={"x-functions-key": os.environ["LASTBUY_EXPORT_FUNCTION_KEY"]},
            timeout=120,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("key") != job["key"]:
            raise ValueError("Export worker returned an unrelated job")
        return result
    except (httpx.HTTPError, ValueError):
        # Never generate a new reference. Worker may have committed after a timeout.
        return {
            "key": job["key"],
            "receipt": None,
            "status": "PENDING",
            "message": "Delivery is unconfirmed. Reconcile this same reference.",
        }
