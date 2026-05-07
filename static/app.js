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
  state.info = info;
  const badge = $("#backend-badge");
  badge.textContent = info.demo ? "Demo data" : "Live · GCS";
  badge.style.color = info.demo ? "var(--text-faint)" : "var(--accent)";

  const pill = $("#auth-pill");
  const text = $("#auth-text");
  if (info.session_authenticated) {
    pill.dataset.mode = "auth";
    text.textContent = info.identity || info.project || "authenticated";
    pill.title = `Authenticated as ${info.identity || "?"} · click to switch`;
  } else if (!info.demo) {
    pill.dataset.mode = "env";
    text.textContent = "env credentials";
    pill.title = "Using server-side credentials · click to override";
  } else {
    pill.dataset.mode = "demo";
    text.textContent = "demo data · sign in";
    pill.title = "Click to upload a service account";
  }
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

function showToast({ name, status = "info", text = "" }) {
  const stack = $("#toast-stack");
  const el = document.createElement("div");
  el.className = "toast " + status;
  el.innerHTML = `
    <span class="name" title="${escapeHtml(name)}">${escapeHtml(name)}</span>
    <span class="pct">${escapeHtml(text)}</span>
    <div class="progress"><span></span></div>
  `;
  stack.appendChild(el);
  return {
    el,
    update(pct, statusText) {
      const bar = el.querySelector(".progress span");
      if (bar) bar.style.width = pct + "%";
      el.querySelector(".pct").textContent = statusText ?? `${pct}%`;
    },
    finish(s) {
      el.classList.remove("info", "error", "ok");
      el.classList.add(s);
      setTimeout(() => el.remove(), s === "error" ? 6000 : 2400);
    },
  };
}

function uploadFiles(fileList) {
  if (!state.bucket || !fileList || !fileList.length) return;
  const bucket = state.bucket;
  const prefix = state.prefix;
  const files = Array.from(fileList);

  let pending = files.length;
  const onAllDone = () => {
    if (pending === 0) loadObjects(true);
  };

  for (const f of files) {
    const toast = showToast({ name: f.name, text: "0%" });
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/object/upload");
    xhr.upload.addEventListener("progress", (ev) => {
      if (ev.lengthComputable) {
        const pct = Math.round((ev.loaded / ev.total) * 100);
        toast.update(pct);
      }
    });
    xhr.addEventListener("load", () => {
      pending--;
      if (xhr.status >= 200 && xhr.status < 300) {
        toast.update(100, "done");
        toast.finish("ok");
      } else {
        let msg = "upload failed";
        try { msg = JSON.parse(xhr.responseText).detail || msg; } catch {}
        toast.update(0, msg);
        toast.finish("error");
      }
      onAllDone();
    });
    xhr.addEventListener("error", () => {
      pending--;
      toast.update(0, "network error");
      toast.finish("error");
      onAllDone();
    });
    const fd = new FormData();
    fd.append("bucket", bucket);
    fd.append("prefix", prefix);
    fd.append("files", f, f.name);
    xhr.send(fd);
  }
}

function setupDragAndDrop() {
  const overlay = $("#drop-overlay");
  const label = $("#drop-target-label");
  let depth = 0;
  const isFileDrag = (ev) =>
    ev.dataTransfer && Array.from(ev.dataTransfer.types || []).includes("Files");

  window.addEventListener("dragenter", (ev) => {
    if (!isFileDrag(ev)) return;
    ev.preventDefault();
    depth++;
    if (state.bucket) {
      overlay.classList.remove("hidden");
      label.textContent = `to gs://${state.bucket}/${state.prefix}`;
    }
  });
  window.addEventListener("dragover", (ev) => {
    if (!isFileDrag(ev)) return;
    ev.preventDefault();
    ev.dataTransfer.dropEffect = "copy";
  });
  window.addEventListener("dragleave", (ev) => {
    if (!isFileDrag(ev)) return;
    depth = Math.max(0, depth - 1);
    if (depth === 0) overlay.classList.add("hidden");
  });
  window.addEventListener("drop", (ev) => {
    if (!isFileDrag(ev)) return;
    ev.preventDefault();
    depth = 0;
    overlay.classList.add("hidden");
    if (!state.bucket) return;
    uploadFiles(ev.dataTransfer.files);
  });
}

function setupUploadButton() {
  const btn = $("#upload-btn");
  const input = $("#upload-input");
  btn.addEventListener("click", () => input.click());
  input.addEventListener("change", () => {
    uploadFiles(input.files);
    input.value = "";
  });
}

function setupAuthDialog() {
  const dlg = $("#auth-dialog");
  const drop = $("#sa-drop");
  const fileInput = $("#sa-file-input");
  const textarea = $("#sa-textarea");
  const status = $("#sa-status");
  const submit = $("#sa-submit");
  const logout = $("#sa-logout");
  const pick = $("#sa-pick");

  let pendingFile = null;

  const reset = () => {
    pendingFile = null;
    textarea.value = "";
    status.textContent = "";
    status.classList.remove("error", "ok");
    drop.classList.remove("error", "dragover");
    drop.querySelector("div").textContent = "Drop SA JSON here";
  };

  const setFile = (file) => {
    pendingFile = file;
    drop.querySelector("div").textContent = file.name;
    status.textContent = `${(file.size / 1024).toFixed(1)} KB selected`;
    status.classList.remove("error");
  };

  $("#auth-pill").addEventListener("click", () => {
    reset();
    if (typeof dlg.showModal === "function") dlg.showModal();
  });

  ["dragenter", "dragover"].forEach((t) =>
    drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("dragover"); })
  );
  ["dragleave", "drop"].forEach((t) =>
    drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("dragover"); })
  );
  drop.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  });
  drop.addEventListener("click", (e) => {
    if (e.target.closest("button")) return;
    fileInput.click();
  });
  pick.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) setFile(fileInput.files[0]);
  });

  submit.addEventListener("click", async () => {
    let body;
    let headers = {};
    if (pendingFile) {
      const fd = new FormData();
      fd.append("file", pendingFile, pendingFile.name);
      body = fd;
    } else if (textarea.value.trim()) {
      body = textarea.value;
      headers["Content-Type"] = "application/json";
    } else {
      status.textContent = "Pick a file or paste JSON first";
      status.classList.add("error");
      return;
    }
    submit.disabled = true;
    try {
      const r = await fetch("/api/auth/sa", { method: "POST", body, headers });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
      status.textContent = `Signed in as ${data.identity}`;
      status.classList.add("ok");
      setTimeout(async () => {
        dlg.close();
        await refreshAll();
      }, 350);
    } catch (e) {
      status.textContent = e.message;
      status.classList.add("error");
    } finally {
      submit.disabled = false;
    }
  });

  logout.addEventListener("click", async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    dlg.close();
    await refreshAll();
  });
}

async function refreshAll() {
  state.bucket = null;
  state.prefix = "";
  await loadInfo();
  await loadBuckets();
}

async function init() {
  setupSearch();
  setupTheme();
  setupDragAndDrop();
  setupUploadButton();
  setupAuthDialog();
  $("#refresh").addEventListener("click", () => loadObjects(true));
  observer.observe($("#sentinel"));
  await loadInfo();
  await loadBuckets();
}

init();
