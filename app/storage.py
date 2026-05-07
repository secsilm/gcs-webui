"""Storage abstraction. The web layer only depends on this protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import BinaryIO, Iterator, Optional, Protocol


@dataclass
class BucketInfo:
    name: str
    location: Optional[str] = None
    storage_class: Optional[str] = None
    created: Optional[str] = None


@dataclass
class ObjectInfo:
    name: str               # full object name including prefix
    size: int = 0
    updated: Optional[str] = None
    content_type: Optional[str] = None
    is_prefix: bool = False  # synthesised "folder"
    etag: Optional[str] = None
    generation: Optional[int] = None
    md5_hash: Optional[str] = None


@dataclass
class ListPage:
    items: list[ObjectInfo] = field(default_factory=list)
    next_page_token: Optional[str] = None
    prefix: str = ""


class Storage(Protocol):
    """Abstract storage interface, satisfied by both GCS and the fake."""

    backend: str
    identity: Optional[str]   # display label e.g. SA email or "demo"
    project: Optional[str]
    read_only: bool

    def list_buckets(self) -> list[BucketInfo]: ...

    def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        delimiter: str = "/",
        page_token: Optional[str] = None,
        page_size: int = 200,
    ) -> ListPage: ...

    def get_object(self, bucket: str, name: str) -> ObjectInfo: ...

    def read_object(self, bucket: str, name: str) -> Iterator[bytes]: ...

    def signed_url(self, bucket: str, name: str, expires_seconds: int = 3600) -> Optional[str]:
        """Return an HTTPS URL for direct download, or None if not supported."""
        ...

    def upload_object(
        self,
        bucket: str,
        name: str,
        stream: BinaryIO,
        content_type: Optional[str] = None,
    ) -> ObjectInfo: ...
