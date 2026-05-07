# gcs-webui

A small, fast web UI for browsing **Google Cloud Storage** buckets — the same
browse-and-download flow as the GCS / S3 web consoles, but trimmed down to
something a Python or Java developer can `docker run` in ten seconds.

* Authentication via service-account JSON (mount it, or pass via env).
* Buckets · folder tree · object metadata · streaming download.
* Handles 1000+ object listings smoothly (server-side paging + infinite scroll).
* Light / dark theme, keyboard-friendly, Chrome-tested.
* No build step, no Node, no SPA bundle. Image is < 200 MB.

## Screenshots

![Bucket overview](tests/screenshots/01-bucket-overview-light.png)
![Drilldown](tests/screenshots/02-folder-drilldown.png)
![Object details](tests/screenshots/04-object-details.png)
![Dark theme](tests/screenshots/05-dark-theme.png)
![1,347 files in one view](tests/screenshots/06-large-listing.png)

## Quick start (Docker)

```bash
# point GOOGLE_APPLICATION_CREDENTIALS at a mounted SA file
docker run --rm -p 8080:8080 \
  -v $PWD/sa.json:/secrets/sa.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/sa.json \
  gcs-webui:latest
```

Then open <http://localhost:8080>.

Or with compose (also enforces read-only fs / dropped caps / 256 MB limit):

```bash
docker compose up --build
```

## Demo mode (no credentials)

Set `GCS_DEMO_MODE=1` to load the in-memory fake dataset (3 buckets, 1500+
objects). Useful for trying the UI before wiring up real credentials.

```bash
docker run --rm -p 8080:8080 -e GCS_DEMO_MODE=1 gcs-webui:latest
```

## Running locally

```bash
pip install -r requirements.txt
GCS_DEMO_MODE=1 uvicorn app.main:app --port 8080
```

## Auth options

| Env var | Effect |
| --- | --- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to SA JSON file (recommended). |
| `GCS_SA_JSON` | Full SA JSON contents inline (Kubernetes secret friendly). |
| `GCS_DEMO_MODE=1` | Skip credentials, serve fake data. |

If none are set the app falls back to demo mode so the UI still loads.

## Tests

```bash
pip install -r requirements-dev.txt
pytest                                      # api smoke tests
python -m tests.screenshot_capture          # regenerates tests/screenshots/
```

The screenshot script boots the app in demo mode and drives Chromium via
Playwright. Set `PLAYWRIGHT_CHROMIUM_PATH` to override the browser binary.

## See also

* [`TECH_STACK.md`](TECH_STACK.md) — design choices and trade-offs.
