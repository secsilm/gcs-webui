"""FastAPI entrypoint for gcs-webui."""
from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .storage import Storage

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def _make_storage() -> Storage:
    if os.environ.get("GCS_DEMO_MODE") == "1":
        from .fake_storage import FakeStorage
        return FakeStorage()
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or os.environ.get("GCS_SA_JSON"):
        from .gcs_storage import GcsStorage
        return GcsStorage.from_env()
    # No credentials configured -> fall back to demo mode so the UI still loads.
    from .fake_storage import FakeStorage
    return FakeStorage()


def create_app(storage: Optional[Storage] = None) -> FastAPI:
    app = FastAPI(title="gcs-webui", docs_url=None, redoc_url=None)
    app.state.storage = storage or _make_storage()

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "backend": getattr(app.state.storage, "backend", "unknown")}

    @app.get("/api/info")
    def info():
        return {
            "backend": getattr(app.state.storage, "backend", "unknown"),
            "demo": getattr(app.state.storage, "backend", "") == "fake",
        }

    @app.get("/api/buckets")
    def list_buckets():
        return [asdict(b) for b in app.state.storage.list_buckets()]

    @app.get("/api/objects")
    def list_objects(
        bucket: str = Query(..., min_length=1),
        prefix: str = "",
        delimiter: str = "/",
        page_token: Optional[str] = None,
        page_size: int = Query(200, ge=1, le=1000),
    ):
        page = app.state.storage.list_objects(
            bucket=bucket,
            prefix=prefix,
            delimiter=delimiter,
            page_token=page_token,
            page_size=page_size,
        )
        return {
            "items": [asdict(i) for i in page.items],
            "next_page_token": page.next_page_token,
            "prefix": page.prefix,
        }

    @app.get("/api/object")
    def get_object(bucket: str, name: str):
        try:
            obj = app.state.storage.get_object(bucket, name)
        except KeyError:
            raise HTTPException(404, "not found")
        return asdict(obj)

    @app.get("/api/object/download")
    def download_object(bucket: str, name: str):
        try:
            obj = app.state.storage.get_object(bucket, name)
        except KeyError:
            raise HTTPException(404, "not found")

        signed = app.state.storage.signed_url(bucket, name)
        if signed:
            return JSONResponse({"redirect": signed})

        filename = name.rsplit("/", 1)[-1] or "download"
        return StreamingResponse(
            app.state.storage.read_object(bucket, name),
            media_type=obj.content_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()
