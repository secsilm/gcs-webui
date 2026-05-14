"""FastAPI entrypoint for gcs-webui."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
)
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .sessions import SessionRegistry
from .storage import Storage

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
COOKIE = "gcs_webui_sid"

# File extensions previewable as plain text when the server-side
# Content-Type isn't a recognisable text/* mime.
PREVIEW_TEXT_EXTENSIONS = {
    "csv", "tsv", "txt", "log", "json", "jsonl", "ndjson",
    "md", "markdown", "rst",
    "xml", "yaml", "yml", "html", "htm",
    "py", "js", "mjs", "ts", "css",
    "sh", "bash", "zsh", "ini", "cfg", "conf", "toml", "sql",
    "rs", "go", "java", "c", "h", "cpp", "hpp",
    "env", "properties", "gitignore", "dockerfile",
}

PREVIEW_TEXT_MIMES = {
    "application/json",
    "application/x-ndjson",
    "application/xml",
    "application/javascript",
    "application/x-yaml",
    "application/x-sh",
    "application/x-shellscript",
    "application/csv",
}


def _is_previewable(name: str, content_type: Optional[str]) -> bool:
    if content_type:
        ct = content_type.split(";", 1)[0].strip().lower()
        if ct.startswith("text/"):
            return True
        if ct in PREVIEW_TEXT_MIMES:
            return True
    base = name.rsplit("/", 1)[-1].lower()
    ext = base.rsplit(".", 1)[-1] if "." in base else base
    return ext in PREVIEW_TEXT_EXTENSIONS


def _make_default_storage() -> Optional[Storage]:
    """Return the storage used when a session has not authenticated.

    Demo mode and env credentials are opt-in. By default the app has no
    server-side storage, and every user must sign in via the UI.

    If env credentials are configured but cannot be loaded (e.g. the JSON
    file isn't mounted), log a warning and continue with no default —
    crashing at boot would mask the problem and prevent users from signing
    in via the UI.
    """
    if os.environ.get("GCS_DEMO_MODE") == "1":
        from .fake_storage import FakeStorage
        return FakeStorage()

    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") or ""
    sa_json = os.environ.get("GCS_SA_JSON") or ""
    if not sa_path and not sa_json:
        return None

    if sa_path and not Path(sa_path).is_file():
        print(
            f"gcs-webui: GOOGLE_APPLICATION_CREDENTIALS={sa_path!r} does not exist; "
            f"continuing without a default storage. Users can still sign in via the UI.",
            file=sys.stderr,
        )
        return None

    try:
        from .gcs_storage import GcsStorage
        return GcsStorage.from_env()
    except Exception as e:
        print(
            f"gcs-webui: failed to initialise default GCS storage: {e}; "
            f"continuing without a default. Users can still sign in via the UI.",
            file=sys.stderr,
        )
        return None


def _http_status_from_gcs(exc: Exception) -> Optional[int]:
    """Best-effort mapping of google.api_core exceptions to an HTTP status."""
    code = getattr(exc, "code", None)
    if isinstance(code, int) and 400 <= code < 600:
        return code
    # google.api_core exceptions sometimes expose `.response.status_code`
    resp = getattr(exc, "response", None)
    sc = getattr(resp, "status_code", None) or getattr(resp, "status", None)
    if isinstance(sc, int) and 400 <= sc < 600:
        return sc
    return None


def _wrap(call):
    """Run a storage call, converting backend errors into HTTPException."""
    try:
        return call()
    except KeyError:
        raise HTTPException(404, "object or bucket not found")
    except HTTPException:
        raise
    except Exception as e:
        status = _http_status_from_gcs(e)
        if status is not None:
            raise HTTPException(status, str(e))
        raise HTTPException(502, f"backend error: {e}")


def create_app(default_storage: Optional[Storage] = None) -> FastAPI:
    app = FastAPI(title="gcs-webui", docs_url=None, redoc_url=None)
    if default_storage is not None:
        app.state.default_storage = default_storage
    else:
        app.state.default_storage = _make_default_storage()
    app.state.sessions = SessionRegistry()

    def get_session_id(request: Request, response: Response) -> str:
        sid = request.cookies.get(COOKIE)
        if not sid:
            sid = app.state.sessions.new_id()
            response.set_cookie(
                COOKIE, sid, httponly=True, samesite="lax", path="/", max_age=24 * 3600
            )
        return sid

    def get_storage(sid: str = Depends(get_session_id)) -> Storage:
        sess = app.state.sessions.get(sid)
        if sess and sess.storage is not None:
            return sess.storage
        if app.state.default_storage is not None:
            return app.state.default_storage
        raise HTTPException(401, "no_credentials")

    @app.get("/healthz")
    def healthz():
        ds = app.state.default_storage
        return {"ok": True, "backend": getattr(ds, "backend", None)}

    @app.get("/api/info")
    def info(sid: str = Depends(get_session_id)):
        sess = app.state.sessions.get(sid)
        storage = (sess.storage if sess and sess.storage else None) or app.state.default_storage
        if storage is None:
            return {
                "backend": None,
                "demo": False,
                "identity": None,
                "project": None,
                "session_authenticated": False,
                "default_available": False,
                "needs_credentials": True,
            }
        return {
            "backend": getattr(storage, "backend", "unknown"),
            "demo": getattr(storage, "backend", "") == "fake",
            "identity": getattr(storage, "identity", None),
            "project": getattr(storage, "project", None),
            "session_authenticated": bool(sess and sess.storage is not None),
            "default_available": app.state.default_storage is not None,
            "needs_credentials": False,
        }

    @app.post("/api/auth/sa")
    async def auth_sa(
        request: Request,
        sid: str = Depends(get_session_id),
        file: Optional[UploadFile] = File(None),
    ):
        if file is not None:
            data = await file.read()
        else:
            data = await request.body()
        try:
            sa_info = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise HTTPException(400, f"Invalid JSON: {e}")

        try:
            from .gcs_storage import GcsStorage
            storage = GcsStorage.from_service_account_info(sa_info)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except Exception as e:
            raise HTTPException(400, f"Could not initialise GCS client: {e}")

        app.state.sessions.set_storage(sid, storage)
        return {
            "ok": True,
            "identity": storage.identity,
            "project": storage.project,
            "backend": storage.backend,
        }

    @app.post("/api/auth/logout")
    def auth_logout(sid: str = Depends(get_session_id)):
        app.state.sessions.clear(sid)
        return {"ok": True}

    @app.get("/api/buckets")
    def list_buckets(storage: Storage = Depends(get_storage)):
        return _wrap(lambda: [asdict(b) for b in storage.list_buckets()])

    @app.get("/api/objects")
    def list_objects(
        bucket: str = Query(..., min_length=1),
        prefix: str = "",
        delimiter: str = "/",
        page_token: Optional[str] = None,
        page_size: int = Query(200, ge=1, le=1000),
        storage: Storage = Depends(get_storage),
    ):
        page = _wrap(lambda: storage.list_objects(
            bucket=bucket,
            prefix=prefix,
            delimiter=delimiter,
            page_token=page_token,
            page_size=page_size,
        ))
        return {
            "items": [asdict(i) for i in page.items],
            "next_page_token": page.next_page_token,
            "prefix": page.prefix,
        }

    @app.get("/api/object")
    def get_object(bucket: str, name: str, storage: Storage = Depends(get_storage)):
        obj = _wrap(lambda: storage.get_object(bucket, name))
        return asdict(obj)

    @app.get("/api/object/download")
    def download_object(bucket: str, name: str, storage: Storage = Depends(get_storage)):
        obj = _wrap(lambda: storage.get_object(bucket, name))

        filename = name.rsplit("/", 1)[-1] or "download"
        safe_filename = filename.replace("\\", "\\\\").replace('"', '\\"')
        disposition = f'attachment; filename="{safe_filename}"'

        signed = None
        try:
            signed = storage.signed_url(bucket, name, response_disposition=disposition)
        except Exception:
            signed = None
        if signed:
            # Redirect so plain <a download> links download the file, not a JSON wrapper.
            return RedirectResponse(signed, status_code=302)

        return StreamingResponse(
            storage.read_object(bucket, name),
            media_type=obj.content_type or "application/octet-stream",
            headers={"Content-Disposition": disposition},
        )

    @app.get("/api/object/preview")
    def preview_object(
        bucket: str,
        name: str,
        lines: int = Query(10, ge=1, le=500),
        max_bytes: int = Query(256 * 1024, ge=1024, le=4 * 1024 * 1024),
        storage: Storage = Depends(get_storage),
    ):
        obj = _wrap(lambda: storage.get_object(bucket, name))
        if not _is_previewable(name, obj.content_type):
            raise HTTPException(415, "preview not supported for this file type")

        buf = bytearray()

        def _read():
            gen = storage.read_object(bucket, name)
            try:
                for chunk in gen:
                    buf.extend(chunk)
                    if len(buf) >= max_bytes or buf.count(b"\n") >= lines:
                        break
            finally:
                close = getattr(gen, "close", None)
                if callable(close):
                    close()

        _wrap(_read)

        try:
            text = buf.decode("utf-8")
            encoding = "utf-8"
        except UnicodeDecodeError:
            text = buf.decode("utf-8", errors="replace")
            encoding = "utf-8-replace"

        all_lines = text.splitlines()
        shown = all_lines[:lines]
        truncated = (
            (obj.size and len(buf) < obj.size)
            or len(all_lines) > lines
        )
        return {
            "content": "\n".join(shown),
            "lines_shown": len(shown),
            "lines_requested": lines,
            "truncated": bool(truncated),
            "total_size": obj.size,
            "bytes_read": len(buf),
            "encoding": encoding,
            "content_type": obj.content_type,
        }

    @app.post("/api/object/upload")
    async def upload_objects(
        bucket: str = Form(...),
        prefix: str = Form(""),
        files: list[UploadFile] = File(...),
        storage: Storage = Depends(get_storage),
    ):
        if getattr(storage, "read_only", False):
            raise HTTPException(403, "current credentials do not allow uploads")
        normalized = (prefix or "").lstrip("/")
        if normalized and not normalized.endswith("/"):
            normalized += "/"
        results = []
        for f in files:
            name = normalized + (f.filename or "untitled")
            info = _wrap(lambda f=f, name=name: storage.upload_object(
                bucket, name, f.file, f.content_type
            ))
            results.append(asdict(info))
        return {"uploaded": results}

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()
