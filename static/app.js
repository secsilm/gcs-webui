// gcs-webui frontend. Vanilla JS, no build step.

const state = {
  buckets: [],
  bucket: null,
  prefix: "",
  rows: [],            // ObjectInfo from API
  nextPageToken: null,
  loading: false,
  filter: "",
};

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const fmtBytes = (n) => {
  if (n == null || isNaN(n)) return "—";
  if (n === 0) return "0 B";
  const u = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.min(u.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
  return (n / Math.pow(1024, i)).toFixed(i ? 1 : 0) + " " + u[i];
};

const fmtDate = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return "—";
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return Math.floor(diff / 60) + " min ago";
  if (diff < 86400) return Math.floor(diff / 3600) + " h ago";
  if (diff < 86400 * 30) return Math.floor(diff / 86400) + " d ago";
  return d.toISOString().slice(0, 10);
};

const ICONS = {
  folder: '<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-8z"/></svg>',
  file:   '<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
  download: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
};

function basename(name) {
  if (name.endsWith("/")) {
    const trimmed = name.slice(0, -1);
    return trimmed.split("/").pop() + "/";
  }
  return name.split("/").pop();
}

function relativeName(item) {
  const tail = item.name.startsWith(state.prefix) ? item.name.slice(state.prefix.length) : item.name;
  return tail || basename(item.name);
}

async function api(path, params) {
  const url = new URL(path, location.origin);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v != null && v !== "") url.searchParams.set(k, v);
    }
  }
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function loadInfo() {
  const info = await api("/api/info");
  const badge = $("#backend-badge");
  badge.textContent = info.demo ? "Demo data" : "Live · GCS";
  badge.style.color = info.demo ? "var(--text-faint)" : "var(--accent)";
}

async function loadBuckets() {
  state.buckets = await api("/api/buckets");
  const ul = $("#bucket-list");
  ul.innerHTML = "";
  for (const b of state.buckets) {
    const li = document.createElement("li");
    li.dataset.name = b.name;
    li.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
        <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v6c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 11v6c0 1.7 4 3 9 3s9-1.3 9-3v-6"/>
      </svg>
      <span>${b.name}</span>
      <small>${b.location ?? ""}</small>
    `;
    li.addEventListener("click", () => selectBucket(b.name));
    ul.appendChild(li);
  }
  if (!state.bucket && state.buckets[0]) {
    selectBucket(state.buckets[0].name);
  }
}

function selectBucket(name) {
  state.bucket = name;
  state.prefix = "";
  for (const li of $$("#bucket-list li")) {
    li.setAttribute("aria-current", li.dataset.name === name ? "true" : "false");
  }
  loadObjects(true);
}

async function loadObjects(reset) {
  if (state.loading || !state.bucket) return;
  state.loading = true;
  if (reset) {
    state.rows = [];
    state.nextPageToken = null;
    $("#rows").innerHTML = "";
  }

  try {
    const page = await api("/api/objects", {
      bucket: state.bucket,
      prefix: state.prefix,
      page_token: reset ? null : state.nextPageToken,
      page_size: 200,
    });
    state.rows = state.rows.concat(page.items);
    state.nextPageToken = page.next_page_token;
    appendRows(page.items);
    renderBreadcrumbs();
    renderStats();
    $("#empty").classList.toggle("hidden", state.rows.length > 0);
  } catch (e) {
    console.error(e);
  } finally {
    state.loading = false;
  }
}

function appendRows(items) {
  const tbody = $("#rows");
  const frag = document.createDocumentFragment();
  for (const it of items) {
    if (state.filter && !it.name.toLowerCase().includes(state.filter)) continue;
    const row = document.createElement("div");
    row.className = "row";
    row.role = "listitem";
    const display = relativeName(it);
    const trimmed = it.is_prefix ? display.replace(/\/$/, "") : display;
    row.innerHTML = `
      <div class="cell col-name ${it.is_prefix ? "is-folder" : ""}">
        ${it.is_prefix ? ICONS.folder : ICONS.file}
        <span class="nm" title="${it.name}">${escapeHtml(trimmed)}</span>
      </div>
      <div class="cell col-size">${it.is_prefix ? "—" : fmtBytes(it.size)}</div>
      <div class="cell col-updated">${it.is_prefix ? "—" : fmtDate(it.updated)}</div>
      <div class="cell col-type">${it.is_prefix ? "folder" : (it.content_type || "—")}</div>
      <div class="cell col-actions">
        ${it.is_prefix ? "" : `<button class="icon-btn" data-action="download" title="Download">${ICONS.download}</button>`}
      </div>
    `;
    row.addEventListener("click", (ev) => {
      if (ev.target.closest('[data-action="download"]')) {
        ev.stopPropagation();
        downloadObject(it.name);
        return;
      }
      if (it.is_prefix) {
        state.prefix = it.name;
        loadObjects(true);
      } else {
        openDetails(it);
      }
    });
    frag.appendChild(row);
  }
  tbody.appendChild(frag);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

function renderBreadcrumbs() {
  const el = $("#breadcrumbs");
  el.innerHTML = "";
  if (!state.bucket) return;

  const make = (label, prefix, current=false) => {
    const span = document.createElement("span");
    span.className = "crumb" + (current ? " current" : "");
    span.textContent = label;
    if (!current) span.addEventListener("click", () => { state.prefix = prefix; loadObjects(true); });
    return span;
  };
  const sep = () => {
    const s = document.createElement("span");
    s.className = "sep";
    s.textContent = "›";
    return s;
  };

  el.appendChild(make("gs://", "", state.prefix === ""));
  el.appendChild(sep());
  el.appendChild(make(state.bucket, "", state.prefix === ""));

  const segs = state.prefix.split("/").filter(Boolean);
  let acc = "";
  for (let i = 0; i < segs.length; i++) {
    el.appendChild(sep());
    acc += segs[i] + "/";
    el.appendChild(make(segs[i], acc, i === segs.length - 1));
  }
}

function renderStats() {
  let folders = 0, files = 0, size = 0;
  for (const r of state.rows) {
    if (r.is_prefix) folders++;
    else { files++; size += r.size || 0; }
  }
  $("#stat-folders").textContent = `${folders.toLocaleString()} folders`;
  $("#stat-files").textContent = `${files.toLocaleString()} files`;
  $("#stat-size").textContent = fmtBytes(size);
}

function downloadObject(name) {
  const url = `/api/object/download?bucket=${encodeURIComponent(state.bucket)}&name=${encodeURIComponent(name)}`;
  fetch(url).then(async (r) => {
    const ct = r.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      const body = await r.json();
      if (body.redirect) { window.open(body.redirect, "_blank"); return; }
    }
    const blob = await r.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = basename(name);
    document.body.appendChild(a);
    a.click();
    a.remove();
  }).catch((e) => alert("Download failed: " + e.message));
}

function openDetails(item) {
  const dlg = $("#object-dialog");
  $("#dlg-name").textContent = item.name;
  $("#dlg-bucket").textContent = state.bucket;
  $("#dlg-size").textContent = `${fmtBytes(item.size)}  (${item.size?.toLocaleString() ?? "?"} bytes)`;
  $("#dlg-type").textContent = item.content_type || "—";
  $("#dlg-updated").textContent = item.updated || "—";
  $("#dlg-generation").textContent = item.generation ?? "—";
  $("#dlg-etag").textContent = item.etag ?? "—";
  const link = $("#dlg-download");
  link.href = `/api/object/download?bucket=${encodeURIComponent(state.bucket)}&name=${encodeURIComponent(item.name)}`;
  link.setAttribute("download", basename(item.name));
  if (typeof dlg.showModal === "function") dlg.showModal();
}

// infinite scroll
const observer = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting && state.nextPageToken && !state.loading) {
      loadObjects(false);
    }
  }
}, { rootMargin: "200px" });

function setupSearch() {
  const input = $("#search-input");
  let t;
  input.addEventListener("input", () => {
    clearTimeout(t);
    t = setTimeout(() => {
      state.filter = input.value.trim().toLowerCase();
      $("#rows").innerHTML = "";
      appendRows(state.rows);
    }, 120);
  });
}

function setupTheme() {
  const saved = localStorage.getItem("gcs-webui-theme");
  if (saved) document.documentElement.setAttribute("data-theme", saved);
  $("#theme-toggle").addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "light";
    const next = cur === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("gcs-webui-theme", next);
  });
}

async function init() {
  setupSearch();
  setupTheme();
  $("#refresh").addEventListener("click", () => loadObjects(true));
  observer.observe($("#sentinel"));
  await loadInfo();
  await loadBuckets();
}

init();
