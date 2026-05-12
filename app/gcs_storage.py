"""Real Google Cloud Storage backend.

Imported lazily so that demo / test deployments don't require credentials.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
from typing import BinaryIO, Iterator, Optional

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
    read_only = False

    def __init__(self, client, identity: Optional[str] = None, project: Optional[str] = None):
        self._client = client
        self.identity = identity
        self.project = project or getattr(client, "project", None)

    @classmethod
    def from_env(cls) -> "GcsStorage":
        json_blob = os.environ.get("GCS_SA_JSON")
        if json_blob:
            return cls.from_service_account_info(json.loads(json_blob))
        # else rely on GOOGLE_APPLICATION_CREDENTIALS / ADC
        from google.cloud import storage as gcs
        return cls(gcs.Client())

    @classmethod
    def from_service_account_info(cls, info: dict) -> "GcsStorage":
        if not isinstance(info, dict) or "client_email" not in info or "private_key" not in info:
            raise ValueError("not a service account JSON: missing client_email/private_key")
        from google.cloud import storage as gcs
        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_info(info)
        project = info.get("project_id")
        return cls(
            gcs.Client(project=project, credentials=creds),
            identity=info.get("client_email"),
            project=project,
        )

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

    def signed_url(
        self,
        bucket: str,
        name: str,
        expires_seconds: int = 3600,
        response_disposition: Optional[str] = None,
    ) -> Optional[str]:
        blob = self._client.bucket(bucket).blob(name)
        try:
            return blob.generate_signed_url(
                version="v4",
                expiration=_dt.timedelta(seconds=expires_seconds),
                method="GET",
                response_disposition=response_disposition,
            )
        except Exception:
            return None

    def upload_object(
        self,
        bucket: str,
        name: str,
        stream: BinaryIO,
        content_type: Optional[str] = None,
    ) -> ObjectInfo:
        blob = self._client.bucket(bucket).blob(name)
        blob.upload_from_file(stream, content_type=content_type, rewind=False)
        blob.reload()
        return ObjectInfo(
            name=blob.name,
            size=blob.size or 0,
            updated=_to_iso(blob.updated),
            content_type=blob.content_type,
            etag=blob.etag,
            generation=blob.generation,
            md5_hash=blob.md5_hash,
        )
