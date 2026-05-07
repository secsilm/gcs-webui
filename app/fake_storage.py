"""In-memory fake storage. Used for demo mode and Playwright tests.

Generates a realistic-looking dataset including a bucket with 1500+ objects
spread across nested folders to validate large-listing performance.
"""
from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import BinaryIO, Iterator, Optional

from .storage import BucketInfo, ListPage, ObjectInfo


def _utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _build_dataset() -> dict[str, dict[str, ObjectInfo]]:
    rng = random.Random(42)
    base = datetime(2025, 1, 1, tzinfo=timezone.utc)

    buckets: dict[str, dict[str, ObjectInfo]] = {
        "demo-app-logs": {},
        "demo-ml-datasets": {},
        "demo-static-assets": {},
    }

    # bucket 1: simulated app logs, ~1600 files across dates and services
    services = ["api-gateway", "billing", "auth", "search", "scheduler"]
    for d in range(60):
        day = base + timedelta(days=d)
        for service in services:
            for hour in range(rng.randint(2, 7)):
                name = (
                    f"logs/{day:%Y/%m/%d}/{service}/"
                    f"{day:%Y%m%d}-{hour:02d}-{rng.randint(0, 9999):04d}.log.gz"
                )
                buckets["demo-app-logs"][name] = ObjectInfo(
                    name=name,
                    size=rng.randint(2_000, 9_500_000),
                    updated=_utc(day + timedelta(hours=hour)),
                    content_type="application/gzip",
                    etag=hashlib.md5(name.encode()).hexdigest(),
                    generation=rng.randint(10**16, 10**17),
                )

    # bucket 2: ML datasets, smaller hierarchy
    for split in ("train", "val", "test"):
        for i in range(rng.randint(40, 120)):
            name = f"vision/cats-vs-dogs/{split}/{i:05d}.jpg"
            buckets["demo-ml-datasets"][name] = ObjectInfo(
                name=name,
                size=rng.randint(80_000, 600_000),
                updated=_utc(base + timedelta(days=rng.randint(0, 90), seconds=rng.randint(0, 86400))),
                content_type="image/jpeg",
                etag=hashlib.md5(name.encode()).hexdigest(),
                generation=rng.randint(10**16, 10**17),
            )
    for name in (
        "vision/README.md",
        "vision/labels.csv",
        "tabular/sales-2024.parquet",
        "tabular/sales-2025.parquet",
        "embeddings/openai-ada-002.jsonl",
    ):
        buckets["demo-ml-datasets"][name] = ObjectInfo(
            name=name,
            size=rng.randint(1_000, 50_000_000),
            updated=_utc(base + timedelta(days=rng.randint(0, 90))),
            content_type="text/plain" if name.endswith(".md") else "application/octet-stream",
            etag=hashlib.md5(name.encode()).hexdigest(),
            generation=rng.randint(10**16, 10**17),
        )

    # bucket 3: static assets
    for kind, ext, ctype in (
        ("img", "png", "image/png"),
        ("img", "svg", "image/svg+xml"),
        ("css", "css", "text/css"),
        ("js", "js", "application/javascript"),
    ):
        for i in range(rng.randint(8, 25)):
            name = f"web/{kind}/asset-{i:03d}.{ext}"
            buckets["demo-static-assets"][name] = ObjectInfo(
                name=name,
                size=rng.randint(500, 250_000),
                updated=_utc(base + timedelta(days=rng.randint(0, 30))),
                content_type=ctype,
                etag=hashlib.md5(name.encode()).hexdigest(),
                generation=rng.randint(10**16, 10**17),
            )
    buckets["demo-static-assets"]["index.html"] = ObjectInfo(
        name="index.html",
        size=4321,
        updated=_utc(base),
        content_type="text/html",
        etag="abc123",
        generation=10**16,
    )
    buckets["demo-static-assets"]["robots.txt"] = ObjectInfo(
        name="robots.txt",
        size=53,
        updated=_utc(base),
        content_type="text/plain",
        etag="def456",
        generation=10**16,
    )

    return buckets


_DATA = _build_dataset()
_BUCKET_META = {
    "demo-app-logs": BucketInfo(
        name="demo-app-logs", location="US", storage_class="STANDARD",
        created="2024-03-12T09:00:00Z",
    ),
    "demo-ml-datasets": BucketInfo(
        name="demo-ml-datasets", location="EU", storage_class="STANDARD",
        created="2024-07-01T08:00:00Z",
    ),
    "demo-static-assets": BucketInfo(
        name="demo-static-assets", location="ASIA", storage_class="NEARLINE",
        created="2025-01-04T12:00:00Z",
    ),
}


class FakeStorage:
    """Minimal in-memory implementation of the Storage protocol."""

    backend = "fake"
    identity = "demo"
    project = "demo-project"
    read_only = False

    def list_buckets(self) -> list[BucketInfo]:
        return list(_BUCKET_META.values())

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str = "/",
        page_token: Optional[str] = None,
        page_size: int = 200,
    ) -> ListPage:
        if bucket not in _DATA:
            return ListPage(prefix=prefix)

        prefixes: set[str] = set()
        files: list[ObjectInfo] = []
        for name, obj in _DATA[bucket].items():
            if not name.startswith(prefix):
                continue
            tail = name[len(prefix):]
            if delimiter and delimiter in tail:
                prefixes.add(prefix + tail.split(delimiter, 1)[0] + delimiter)
            else:
                files.append(obj)

        all_items: list[ObjectInfo] = [
            ObjectInfo(name=p, is_prefix=True) for p in sorted(prefixes)
        ] + sorted(files, key=lambda o: o.name)

        start = int(page_token) if page_token else 0
        end = start + page_size
        items = all_items[start:end]
        next_token = str(end) if end < len(all_items) else None
        return ListPage(items=items, next_page_token=next_token, prefix=prefix)

    def get_object(self, bucket: str, name: str) -> ObjectInfo:
        if bucket not in _DATA or name not in _DATA[bucket]:
            raise KeyError(f"{bucket}/{name} not found")
        return _DATA[bucket][name]

    def read_object(self, bucket: str, name: str) -> Iterator[bytes]:
        info = self.get_object(bucket, name)
        # synthesise content based on mime type so previews render reasonably
        if info.content_type and info.content_type.startswith("text/"):
            payload = (
                f"# {name}\n\nThis is fake demo content generated by gcs-webui's "
                f"FakeStorage backend.\nSize header: {info.size} bytes.\n"
            ).encode()
        else:
            payload = b"\x00" * min(info.size, 1024)
        yield payload

    def signed_url(self, bucket: str, name: str, expires_seconds: int = 3600) -> Optional[str]:
        return None

    def upload_object(self, bucket, name, stream, content_type=None):
        if bucket not in _DATA:
            raise KeyError(f"bucket {bucket} not found")
        data = stream.read()
        info = ObjectInfo(
            name=name,
            size=len(data),
            updated=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            content_type=content_type or "application/octet-stream",
            etag=hashlib.md5(data).hexdigest(),
            generation=int(datetime.now(timezone.utc).timestamp() * 1_000_000),
        )
        _DATA[bucket][name] = info
        return info
