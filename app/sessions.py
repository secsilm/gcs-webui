"""Per-browser-session storage registry.

A single uvicorn worker can serve multiple users at once. Each browser gets a
random `gcs_webui_sid` cookie; that ID maps to a `Session` holding their
authenticated `Storage` instance (or `None`, meaning fall back to the default
storage configured at startup).

Session state is in-memory only — credentials never touch disk.
"""
from __future__ import annotations

import secrets
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

from .storage import Storage


@dataclass
class Session:
    storage: Optional[Storage]
    created_at: float
    last_used_at: float


class SessionRegistry:
    def __init__(self, max_sessions: int = 64, idle_seconds: int = 24 * 3600):
        self._lock = threading.Lock()
        self._sessions: "OrderedDict[str, Session]" = OrderedDict()
        self._max = max_sessions
        self._idle = idle_seconds

    def new_id(self) -> str:
        return secrets.token_urlsafe(24)

    def get(self, sid: str) -> Optional[Session]:
        with self._lock:
            self._evict()
            sess = self._sessions.get(sid)
            if sess:
                sess.last_used_at = time.time()
                self._sessions.move_to_end(sid)
            return sess

    def set_storage(self, sid: str, storage: Optional[Storage]) -> Session:
        with self._lock:
            self._evict()
            now = time.time()
            sess = self._sessions.get(sid)
            if sess is None:
                sess = Session(storage=storage, created_at=now, last_used_at=now)
                self._sessions[sid] = sess
            else:
                sess.storage = storage
                sess.last_used_at = now
                self._sessions.move_to_end(sid)
            while len(self._sessions) > self._max:
                self._sessions.popitem(last=False)
            return sess

    def clear(self, sid: str) -> None:
        with self._lock:
            self._sessions.pop(sid, None)

    def _evict(self) -> None:
        cutoff = time.time() - self._idle
        stale = [k for k, v in self._sessions.items() if v.last_used_at < cutoff]
        for k in stale:
            self._sessions.pop(k, None)
