"""Lightweight pytest covering the API surface against fake data."""
from __future__ import annotations

import asyncio

import httpx
import pytest

from app.fake_storage import FakeStorage
from app.main import create_app


@pytest.fixture
def client():
    app = create_app(FakeStorage())
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_healthz(client):
    async def _():
        async with client as c:
            r = await c.get("/healthz")
            assert r.status_code == 200
            assert r.json()["ok"] is True
    _run(_())


def test_buckets(client):
    async def _():
        async with client as c:
            r = await c.get("/api/buckets")
            assert r.status_code == 200
            names = [b["name"] for b in r.json()]
            assert "demo-app-logs" in names
            assert len(names) >= 3
    _run(_())


def test_objects_paginate_through_thousand_plus(client):
    async def _():
        async with client as c:
            total, token = 0, None
            for _ in range(20):
                params = {
                    "bucket": "demo-app-logs",
                    "prefix": "logs/",
                    "delimiter": "",
                    "page_size": 200,
                }
                if token:
                    params["page_token"] = token
                r = await c.get("/api/objects", params=params)
                assert r.status_code == 200
                payload = r.json()
                total += len(payload["items"])
                token = payload["next_page_token"]
                if not token:
                    break
            assert total > 1000, f"expected >1000 objects, got {total}"
    _run(_())


def test_object_details(client):
    async def _():
        async with client as c:
            r = await c.get("/api/object", params={
                "bucket": "demo-static-assets",
                "name": "index.html",
            })
            assert r.status_code == 200
            data = r.json()
            assert data["name"] == "index.html"
            assert data["size"] > 0
    _run(_())


def test_object_download_streams(client):
    async def _():
        async with client as c:
            r = await c.get("/api/object/download", params={
                "bucket": "demo-static-assets",
                "name": "index.html",
            })
            assert r.status_code == 200
            assert "attachment" in r.headers.get("content-disposition", "")
            assert len(r.content) > 0
    _run(_())


def test_session_cookie_assigned(client):
    async def _():
        async with client as c:
            r = await c.get("/api/info")
            assert r.status_code == 200
            assert "gcs_webui_sid" in r.cookies
            assert r.json()["session_authenticated"] is False
    _run(_())


def test_upload_then_listed(client):
    async def _():
        async with client as c:
            r = await c.post(
                "/api/object/upload",
                data={"bucket": "demo-static-assets", "prefix": "uploads/"},
                files={"files": ("hello.txt", b"hello world", "text/plain")},
            )
            assert r.status_code == 200, r.text
            uploaded = r.json()["uploaded"]
            assert uploaded[0]["name"] == "uploads/hello.txt"
            assert uploaded[0]["size"] == 11
            r2 = await c.get("/api/objects", params={
                "bucket": "demo-static-assets",
                "prefix": "uploads/",
                "delimiter": "",
            })
            names = [i["name"] for i in r2.json()["items"]]
            assert "uploads/hello.txt" in names
    _run(_())


def test_preview_small_csv_shows_all_lines(client):
    """A small file that fits within max_bytes should preview in full,
    not be capped to the default 10-line window."""
    async def _():
        async with client as c:
            csv_lines = [f"col1,col2,col{i}" for i in range(25)]
            csv_payload = "\n".join(csv_lines).encode()
            r = await c.post(
                "/api/object/upload",
                data={"bucket": "demo-static-assets", "prefix": "previews/"},
                files={"files": ("rows.csv", csv_payload, "text/csv")},
            )
            assert r.status_code == 200, r.text

            r = await c.get("/api/object/preview", params={
                "bucket": "demo-static-assets",
                "name": "previews/rows.csv",
            })
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["lines_shown"] == 25
            assert data["truncated"] is False
            assert data["content"].splitlines()[0] == "col1,col2,col0"
            assert data["content"].splitlines()[-1] == "col1,col2,col24"
    _run(_())


def test_preview_truncates_when_file_exceeds_max_bytes(client):
    async def _():
        async with client as c:
            csv_lines = [f"col1,col2,col{i}" for i in range(200)]
            csv_payload = "\n".join(csv_lines).encode()
            await c.post(
                "/api/object/upload",
                data={"bucket": "demo-static-assets", "prefix": "previews/"},
                files={"files": ("big.csv", csv_payload, "text/csv")},
            )
            # Force truncation by setting max_bytes well below the file size.
            r = await c.get("/api/object/preview", params={
                "bucket": "demo-static-assets",
                "name": "previews/big.csv",
                "max_bytes": 128,
                "lines": 10,
            })
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["truncated"] is True
            assert 1 <= data["lines_shown"] <= 10
            assert data["content"].splitlines()[0] == "col1,col2,col0"
    _run(_())


def test_preview_short_file_not_truncated(client):
    async def _():
        async with client as c:
            payload = b"a\nb\nc\n"
            await c.post(
                "/api/object/upload",
                data={"bucket": "demo-static-assets", "prefix": "previews/"},
                files={"files": ("tiny.txt", payload, "text/plain")},
            )
            r = await c.get("/api/object/preview", params={
                "bucket": "demo-static-assets",
                "name": "previews/tiny.txt",
            })
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["lines_shown"] == 3
            assert data["truncated"] is False
    _run(_())


def test_preview_exact_line_count_not_truncated(client):
    """A file with exactly `lines` rows shouldn't be flagged truncated."""
    async def _():
        async with client as c:
            payload = ("\n".join(f"row{i}" for i in range(10)) + "\n").encode()
            await c.post(
                "/api/object/upload",
                data={"bucket": "demo-static-assets", "prefix": "previews/"},
                files={"files": ("exactly10.csv", payload, "text/csv")},
            )
            r = await c.get("/api/object/preview", params={
                "bucket": "demo-static-assets",
                "name": "previews/exactly10.csv",
            })
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["lines_shown"] == 10
            assert data["truncated"] is False
    _run(_())


def test_preview_unsupported_type(client):
    async def _():
        async with client as c:
            r = await c.get("/api/object/preview", params={
                "bucket": "demo-ml-datasets",
                "name": "vision/cats-vs-dogs/train/00000.jpg",
            })
            assert r.status_code == 415
    _run(_())


def test_preview_by_extension_when_octet_stream(client):
    async def _():
        async with client as c:
            # Upload a CSV labelled as application/octet-stream — falls back to extension
            payload = b"a,b,c\n1,2,3\n"
            await c.post(
                "/api/object/upload",
                data={"bucket": "demo-static-assets", "prefix": "previews/"},
                files={"files": ("by-ext.csv", payload, "application/octet-stream")},
            )
            r = await c.get("/api/object/preview", params={
                "bucket": "demo-static-assets",
                "name": "previews/by-ext.csv",
            })
            assert r.status_code == 200
            assert r.json()["lines_shown"] == 2
    _run(_())


def test_bad_sa_rejected():
    # Each call gets a fresh app to keep sessions isolated
    app = create_app(FakeStorage())
    transport = httpx.ASGITransport(app=app)

    async def _():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            r = await c.post("/api/auth/sa", content=b"not json")
            assert r.status_code == 400
            r = await c.post("/api/auth/sa", content=b'{"hello":"world"}')
            assert r.status_code == 400
    _run(_())


def test_no_default_returns_needs_credentials():
    """With no env / demo, /api/info reports needs_credentials and /api/buckets is 401."""
    app = create_app(None)  # explicitly no default
    t = httpx.ASGITransport(app=app)

    async def _():
        async with httpx.AsyncClient(transport=t, base_url="http://test") as c:
            r = await c.get("/api/info")
            assert r.status_code == 200
            data = r.json()
            assert data["needs_credentials"] is True
            assert data["default_available"] is False
            r = await c.get("/api/buckets")
            assert r.status_code == 401
            assert "no_credentials" in r.json()["detail"]
    _run(_())


def test_default_available_flag_when_demo_storage():
    app = create_app(FakeStorage())
    t = httpx.ASGITransport(app=app)

    async def _():
        async with httpx.AsyncClient(transport=t, base_url="http://test") as c:
            data = (await c.get("/api/info")).json()
            assert data["default_available"] is True
            assert data["needs_credentials"] is False
    _run(_())


def test_missing_sa_file_does_not_crash_startup(monkeypatch):
    """If GOOGLE_APPLICATION_CREDENTIALS points to a non-existent file the app
    must still start and report needs_credentials, instead of raising at boot."""
    from app import main as main_module
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/nonexistent/sa.json")
    monkeypatch.delenv("GCS_SA_JSON", raising=False)
    monkeypatch.delenv("GCS_DEMO_MODE", raising=False)
    storage = main_module._make_default_storage()
    assert storage is None  # gracefully fell back

    app = main_module.create_app()
    t = httpx.ASGITransport(app=app)

    async def _():
        async with httpx.AsyncClient(transport=t, base_url="http://test") as c:
            data = (await c.get("/api/info")).json()
            assert data["needs_credentials"] is True
    _run(_())


def test_backend_403_propagates_to_http():
    """A storage that raises a Forbidden-like exception surfaces as HTTP 403."""
    class Forbidden(Exception):
        code = 403

    class StubStorage(FakeStorage):
        def list_objects(self, *a, **kw):
            raise Forbidden("does not have storage.objects.list access")

    app = create_app(StubStorage())
    t = httpx.ASGITransport(app=app)

    async def _():
        async with httpx.AsyncClient(transport=t, base_url="http://test") as c:
            r = await c.get("/api/objects", params={"bucket": "x"})
            assert r.status_code == 403
            assert "storage.objects.list" in r.json()["detail"]
    _run(_())


def test_sessions_isolated_per_cookie():
    """Two clients with different cookies don't share auth state."""
    app = create_app(FakeStorage())
    t = httpx.ASGITransport(app=app)

    async def _():
        async with httpx.AsyncClient(transport=t, base_url="http://test") as c1, \
                   httpx.AsyncClient(transport=t, base_url="http://test") as c2:
            # client 1 starts a session
            await c1.get("/api/info")
            sid1 = c1.cookies.get("gcs_webui_sid")
            await c2.get("/api/info")
            sid2 = c2.cookies.get("gcs_webui_sid")
            assert sid1 and sid2 and sid1 != sid2
            # client 1 logs out (no-op) — does not touch client 2
            await c1.post("/api/auth/logout")
            r2 = await c2.get("/api/info")
            assert r2.status_code == 200
    _run(_())
