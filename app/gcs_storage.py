"""Real Google Cloud Storage backend.

Imported lazily so that demo / test deployments don't require credentials.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Iterator, Optional

from .storage import BucketInfo, ListPage, ObjectInfo


def _to_iso(value) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        return value.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return str(value)


class GcsStorage:
    """Storage implementation backed by google-cloud-storage."""

    backend = "gcs"

    def __init__(self, client):
        self._client = client

    @classmethod
    def from_env(cls) -> "GcsStorage":
        from google.cloud import storage as gcs  # local import keeps fake mode dep-free
        from google.oauth2 import service_account

        json_blob = os.environ.get("GCS_SA_JSON")
        if json_blob:
            info = json.loads(json_blob)
            creds = service_account.Credentials.from_service_account_info(info)
            project = info.get("project_id")
            return cls(gcs.Client(project=project, credentials=creds))

        # else rely on GOOGLE_APPLICATION_CREDENTIALS / ADC
        return cls(gcs.Client())

    def list_buckets(self) -> list[BucketInfo]:
        return [
            BucketInfo(
                name=b.name,
                location=b.location,
                storage_class=b.storage_class,
                created=_to_iso(b.time_created),
            )
            for b in self._client.list_buckets()
        ]

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str = "/",
        page_token: Optional[str] = None,
        page_size: int = 200,
    ) -> ListPage:
        iterator = self._client.list_blobs(
            bucket,
            prefix=prefix,
            delimiter=delimiter,
            max_results=page_size,
            page_token=page_token,
        )
        page = next(iterator.pages)
        files = [
            ObjectInfo(
                name=b.name,
                size=b.size or 0,
                updated=_to_iso(b.updated),
                content_type=b.content_type,
                etag=b.etag,
                generation=b.generation,
                md5_hash=b.md5_hash,
            )
            for b in page
        ]
        prefixes = [
            ObjectInfo(name=p, is_prefix=True) for p in sorted(iterator.prefixes or [])
        ]
        return ListPage(
            items=prefixes + files,
            next_page_token=iterator.next_page_token,
            prefix=prefix,
        )

    def get_object(self, bucket: str, name: str) -> ObjectInfo:
        b = self._client.bucket(bucket).get_blob(name)
        if b is None:
            raise KeyError(f"{bucket}/{name} not found")
        return ObjectInfo(
            name=b.name,
            size=b.size or 0,
            updated=_to_iso(b.updated),
            content_type=b.content_type,
            etag=b.etag,
            generation=b.generation,
            md5_hash=b.md5_hash,
        )

    def read_object(self, bucket: str, name: str) -> Iterator[bytes]:
        blob = self._client.bucket(bucket).blob(name)
        with blob.open("rb") as fh:
            while True:
                chunk = fh.read(1 << 20)
                if not chunk:
                    break
                yield chunk

    def signed_url(self, bucket: str, name: str, expires_seconds: int = 3600) -> Optional[str]:
        blob = self._client.bucket(bucket).blob(name)
        try:
            return blob.generate_signed_url(
                version="v4",
                expiration=_dt.timedelta(seconds=expires_seconds),
                method="GET",
            )
        except Exception:
            return None
