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

        # back to light for the remaining screenshots
        page.click("#theme-toggle")
        page.wait_for_timeout(120)

        # 5b. Credentials dialog (drag SA JSON or paste)
        page.click("#auth-pill")
        page.wait_for_selector("#auth-dialog[open]", timeout=3000)
        # expand the "Paste JSON" section before filling it
        page.evaluate("document.querySelector('#auth-dialog details').open = true")
        page.fill("#sa-textarea", (
            '{\n'
            '  "type": "service_account",\n'
            '  "client_email": "ci-readonly@example-prod.iam.gserviceaccount.com",\n'
            '  "project_id": "example-prod",\n'
            '  "private_key_id": "abc123…",\n'
            '  "private_key": "-----BEGIN PRIVATE KEY-----\\n…\\n-----END PRIVATE KEY-----\\n"\n'
            '}'
        ))
        page.evaluate("document.getElementById('sa-status').textContent = '已解析 · 检测到 5 个字段'")
        page.wait_for_timeout(150)
        _shoot(page, "07-credentials-dialog.png")
        page.evaluate("document.getElementById('auth-dialog').close()")

        # 5c. Drag-drop overlay simulation — set the overlay visible to capture it
        page.evaluate("""
            const o = document.getElementById('drop-overlay');
            o.classList.remove('hidden');
            document.getElementById('drop-target-label').textContent =
                '上传到 gs://demo-static-assets/web/';
        """)
        page.wait_for_timeout(100)
        _shoot(page, "08-drag-drop-overlay.png")
        page.evaluate("document.getElementById('drop-overlay').classList.add('hidden')")

        # 5d. Trigger an upload via API + render an in-progress toast
        page.evaluate("""async () => {
            const stack = document.getElementById('toast-stack');
            const make = (name, pct, status='info') => {
                const t = document.createElement('div');
                t.className = 'toast ' + status;
                t.innerHTML = `
                    <span class="name">${name}</span>
                    <span class="pct">${status === 'ok' ? '完成' : pct + '%'}</span>
                    <div class="progress"><span style="width:${pct}%"></span></div>`;
                stack.appendChild(t);
            };
            make('release-notes.md', 100, 'ok');
            make('build-artifact.tar.gz', 64);
            make('config.yaml', 28);
        }""")
        # Also actually upload one file via API to land in fake storage and refresh listing
        page.evaluate("""async () => {
            const fd = new FormData();
            fd.append('bucket', 'demo-static-assets');
            fd.append('prefix', 'web/');
            const blob = new Blob(['hello from playwright'], { type: 'text/plain' });
            fd.append('files', blob, 'release-notes.md');
            await fetch('/api/object/upload', { method: 'POST', body: fd });
        }""")
        # navigate to that prefix to show the uploaded file
        page.locator("#bucket-list li[data-name='demo-static-assets']").click()
        page.wait_for_timeout(300)
        page.evaluate("""
            const folder = [...document.querySelectorAll('#rows .row')]
                .find(r => r.textContent.includes('web'));
            if (folder) folder.click();
        """)
        page.wait_for_timeout(400)
        _shoot(page, "09-upload-progress.png")
        # clear any toasts before the next screenshot
        page.evaluate("document.getElementById('toast-stack').innerHTML = ''")

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
                document.getElementById('stat-folders').textContent = '0 个文件夹';
                document.getElementById('stat-files').textContent = rows.length.toLocaleString() + ' 个文件';
            }"""
        )
        page.wait_for_timeout(200)
        _shoot(page, "06-large-listing.png")

        # 7. English mode — flip the language toggle to show parity with zh
        page.click("#lang-toggle")
        page.wait_for_timeout(150)
        _shoot(page, "10-english-toggle.png")

        browser.close()
    print("done.")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    capture()
