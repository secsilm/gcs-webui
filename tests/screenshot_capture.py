"""End-to-end screenshot capture against fake data.

Boots the FastAPI app in a background thread (demo mode), drives it with
Playwright/Chromium and saves screenshots to tests/screenshots/.

Run directly:

    GCS_DEMO_MODE=1 python -m tests.screenshot_capture
"""
from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "tests" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)

PORT = int(os.environ.get("GCS_WEBUI_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"
EXEC = os.environ.get(
    "PLAYWRIGHT_CHROMIUM_PATH",
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
)


class _Server:
    def __init__(self):
        os.environ["GCS_DEMO_MODE"] = "1"
        from app.main import create_app
        self.config = uvicorn.Config(
            create_app(), host="127.0.0.1", port=PORT, log_level="warning"
        )
        self.server = uvicorn.Server(self.config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def __enter__(self):
        self.thread.start()
        for _ in range(80):
            if self.server.started:
                return self
            time.sleep(0.05)
        raise RuntimeError("server failed to start")

    def __exit__(self, *exc):
        self.server.should_exit = True
        self.thread.join(timeout=5)


def _shoot(page, name: str):
    out = SHOTS / name
    page.screenshot(path=str(out), full_page=False)
    print(f"  saved {out.relative_to(ROOT)}")


def _wait_rows(page):
    page.wait_for_function(
        "document.querySelectorAll('#rows .row').length > 0",
        timeout=10000,
    )


def _click_first_folder(page):
    page.locator("#rows .row").filter(
        has=page.locator(".col-name.is-folder")
    ).first.click()


def capture():
    print(f"capturing screenshots into {SHOTS.relative_to(ROOT)}")
    with _Server(), sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=EXEC)
        context = browser.new_context(viewport={"width": 1440, "height": 900})

        # 1. Light theme, root of bucket list (default = first bucket)
        page = context.new_page()
        page.goto(BASE)
        page.wait_for_selector("#bucket-list li")
        _wait_rows(page)
        _shoot(page, "01-bucket-overview-light.png")

        # 2. Drill down to a folder-only level: logs/ > 2025/ > 01/
        page.locator("#bucket-list li[data-name='demo-app-logs']").click()
        _wait_rows(page)
        _click_first_folder(page); _wait_rows(page)  # logs/
        _click_first_folder(page); _wait_rows(page)  # 2025/
        _click_first_folder(page); _wait_rows(page)  # 01/
        _shoot(page, "02-folder-drilldown.png")

        # Drill 2 more levels to reach actual files (api-gateway/)
        _click_first_folder(page); _wait_rows(page)  # 01/ (day)
        _click_first_folder(page); _wait_rows(page)  # api-gateway/

        # 3. Search filter on file names
        page.fill("#search-input", "20250101-02")
        page.wait_for_timeout(300)
        _shoot(page, "03-search-filter.png")
        page.fill("#search-input", "")
        page.wait_for_timeout(150)

        # 4. Object details dialog (click a file row)
        page.locator("#rows .row").filter(
            has_not=page.locator(".col-name.is-folder")
        ).first.click()
        page.wait_for_selector("#object-dialog[open]", timeout=5000)
        page.wait_for_timeout(150)
        _shoot(page, "04-object-details.png")
        page.evaluate("document.getElementById('object-dialog').close()")

        # 5. ML datasets bucket in dark theme
        page.locator("#bucket-list li[data-name='demo-ml-datasets']").click()
        _wait_rows(page)
        page.click("#theme-toggle")
        page.wait_for_timeout(150)
        _shoot(page, "05-dark-theme.png")

        # 6. Large listing — back to logs, scroll to load >1000 rows
        page.click("#theme-toggle")  # back to light
        page.locator("#bucket-list li[data-name='demo-app-logs']").click()
        _wait_rows(page)
        _click_first_folder(page); _wait_rows(page)  # logs/
        _click_first_folder(page); _wait_rows(page)  # 2025/
        _click_first_folder(page); _wait_rows(page)  # 01/

        # Switch to flat view so all 1000+ logs come back through paging.
        # We do this by listing without delimiter via direct API hit.
        page.evaluate(
            """async () => {
                window.__rows = [];
                let token = null;
                for (let i = 0; i < 12; i++) {
                    const u = new URL('/api/objects', location.origin);
                    u.searchParams.set('bucket', 'demo-app-logs');
                    u.searchParams.set('prefix', 'logs/');
                    u.searchParams.set('delimiter', '');
                    u.searchParams.set('page_size', '200');
                    if (token) u.searchParams.set('page_token', token);
                    const r = await (await fetch(u)).json();
                    window.__rows.push(...r.items);
                    token = r.next_page_token;
                    if (!token) break;
                }
                return window.__rows.length;
            }"""
        )
        # Render via the existing UI helpers by setting state and rebuilding.
        page.evaluate(
            """() => {
                document.getElementById('rows').innerHTML = '';
                const rows = window.__rows;
                const tbody = document.getElementById('rows');
                const fmtBytes = (n) => {
                    if (!n) return '0 B';
                    const u = ['B','KB','MB','GB','TB'];
                    const i = Math.min(u.length-1, Math.floor(Math.log(n)/Math.log(1024)));
                    return (n/Math.pow(1024,i)).toFixed(i?1:0) + ' ' + u[i];
                };
                const fmtDate = (iso) => iso ? new Date(iso).toISOString().slice(0,10) : '—';
                const frag = document.createDocumentFragment();
                for (const it of rows.slice(0, 600)) {
                    const row = document.createElement('div');
                    row.className = 'row';
                    row.innerHTML = `
                        <div class="cell col-name">
                          <svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                          <span class="nm">${it.name.split('/').pop()}</span>
                        </div>
                        <div class="cell col-size">${fmtBytes(it.size)}</div>
                        <div class="cell col-updated">${fmtDate(it.updated)}</div>
                        <div class="cell col-type">${it.content_type || '—'}</div>
                        <div class="cell col-actions"></div>`;
                    frag.appendChild(row);
                }
                tbody.appendChild(frag);
                document.getElementById('stat-folders').textContent = '0 folders';
                document.getElementById('stat-files').textContent = rows.length.toLocaleString() + ' files';
            }"""
        )
        page.wait_for_timeout(200)
        _shoot(page, "06-large-listing.png")

        browser.close()
    print("done.")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    capture()
