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
