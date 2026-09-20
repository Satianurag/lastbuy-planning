"""Content-addressed snapshots in Azure Blob; no keys or public access links."""

import os

from azure.core.exceptions import ResourceExistsError
from azure.identity import AzureCliCredential, DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

from .domain import Snapshot, canonical, digest


class BlobArchive:
    def __init__(self, client=None):
        self.credential = None
        if client is None:
            self.credential = (
                AzureCliCredential(process_timeout=60)
                if os.getenv("LASTBUY_LOCAL_PROBE") == "1"
                else DefaultAzureCredential()
            )
            client = BlobServiceClient(
                os.environ["LASTBUY_ARCHIVE_URL"], credential=self.credential
            )
        self.client = client
        self.container = os.getenv("LASTBUY_ARCHIVE_CONTAINER", "snapshots")

    def put(self, snapshot: Snapshot):
        sha = digest(snapshot)
        name = f"{snapshot.organization}/{snapshot.case_id}/{sha}.json"
        blob = self.client.get_blob_client(self.container, name)
        try:
            blob.upload_blob(
                canonical(snapshot).encode(),
                overwrite=False,
                content_settings=ContentSettings(content_type="application/json"),
                metadata={"snapshot_sha256": sha},
            )
        except ResourceExistsError:
            # A matching name is insufficient: verify actual stored content before reuse.
            pass
        stored = Snapshot.model_validate_json(blob.download_blob().readall())
        if digest(stored) != sha:
            raise ValueError("Archived snapshot does not match its content address")
        properties = blob.get_blob_properties()
        return {
            "container": self.container,
            "blob": name,
            "snapshot_sha256": sha,
            "etag": properties.etag,
            "version_id": properties.version_id,
            "retention": "content-addressed; production WORM policy configured separately",
        }

    def verify(self, receipt, snapshot):
        expected = f"{snapshot.organization}/{snapshot.case_id}/{digest(snapshot)}.json"
        if (
            receipt.get("blob") != expected
            or receipt.get("container") != self.container
        ):
            raise ValueError("Archive receipt scope mismatch")
        blob = self.client.get_blob_client(self.container, expected)
        stored = Snapshot.model_validate_json(blob.download_blob().readall())
        if digest(stored) != digest(snapshot):
            raise ValueError("Archive contents changed")

    def close(self):
        self.client.close()
        if self.credential:
            self.credential.close()
