"""Separate export identity. Receives an outbox key, never model-authored order data."""

import json
import os
import re
from functools import lru_cache

import azure.functions as func

from lastbuy.archive import BlobArchive
from lastbuy.service import DomainError, Workflow
from lastbuy.sql_erp import SQLSyntheticERP
from lastbuy.store import Store

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@lru_cache
def workflow():
    return Workflow(
        Store(os.environ["LASTBUY_DATABASE_URL"], initialize=False),
        None,
        SQLSyntheticERP(os.environ["LASTBUY_ERP_DATABASE_URL"]),
        archive=BlobArchive(),
    )


@app.route(route="exports/{key}", methods=["POST"])
def export(req: func.HttpRequest):
    key = req.route_params["key"]
    if not re.fullmatch(r"[0-9a-f]{64}", key):
        return func.HttpResponse("Invalid outbox key", status_code=400)
    try:
        receipt = workflow().dispatch(key)
        return func.HttpResponse(
            json.dumps(
                {
                    "key": key,
                    "receipt": receipt,
                    "status": "COMPLETE" if receipt else "UNCERTAIN",
                }
            ),
            mimetype="application/json",
        )
    except DomainError as error:
        return func.HttpResponse(
            json.dumps({"detail": error.message}),
            status_code=error.status,
            mimetype="application/json",
        )
