// gcs-webui frontend. Vanilla JS, no build step.

const I18N = {
  zh: {
    loading: "加载中…",
    buckets: "存储桶",
    theme: "主题",
    docs: "文档",
    upload: "上传",
    refresh: "刷新",
    col_name: "名称",
    col_size: "大小",
    col_modified: "修改时间",
    col_type: "类型",
    empty: "该路径下暂无对象。",
    drop_title: "拖拽文件以上传",
    drop_target_default: "上传到 gs://…",
    drop_target_to: "上传到 gs://{path}",
    auth_title: "Service Account 凭据",
    auth_help: "拖拽一个 Google Cloud service account .json 文件，或粘贴其内容、从磁盘选择。凭据仅保存在本会话内存中，永不写入磁盘。",
    sa_drop_default: "将 SA JSON 拖到此处",
    or: "或",
    pick_file: "选择文件",
    paste_json: "粘贴 JSON",
    use_demo: "使用演示数据",
    authenticate: "登录",
    cancel: "取消",
    close: "关闭",
    download: "下载",
    copy_uri: "复制 URI",
    uri_copied: "已复制 {uri}",
    copy_failed: "复制失败：{msg}",
    detail_bucket: "存储桶",
    detail_size: "大小",
    detail_type: "类型",
    detail_updated: "更新时间",
    detail_generation: "版本号",
    detail_etag: "ETag",
    backend_demo: "演示数据",
    backend_live: "已连接 · GCS",
    pill_demo: "演示数据 · 登录",
    pill_env: "SA 凭据",
    pill_needs: "请登录",
    pill_demo_title: "点击以上传 service account",
    pill_env_title: "正在使用 SA 凭据，点击可覆盖",
    pill_needs_title: "尚未登录，点击以上传 service account",
    pill_auth_title: "已登录 {who} · 点击可切换",
    auth_pill_title: "切换 Service Account",
    theme_title: "切换主题",
    lang_title: "切换语言",
    upload_title: "上传文件（也可拖入页面任意位置）",
    refresh_title: "刷新",
    search_placeholder: "按名称过滤…",
    folders_n: "{n} 个文件夹",
    files_n: "{n} 个文件",
    folder_type: "文件夹",
    just_now: "刚刚",
    min_ago: "{n} 分钟前",
    h_ago: "{n} 小时前",
    d_ago: "{n} 天前",
    bytes_n: "{n} 字节",
    toast_done: "完成",
    toast_failed: "上传失败",
    toast_net_err: "网络错误",
    pick_or_paste: "请先选择文件或粘贴 JSON",
    signed_in_as: "已登录：{who}",
    selected_size: "已选择 {kb} KB",
    download_failed: "下载失败：{msg}",
    error_generic: "请求失败",
    error_401: "尚未登录，请先点击侧边栏凭据胶囊上传 service account",
    error_403: "权限不足，请检查 service account 是否拥有该 bucket 的 storage.objects.list 等权限",
    error_404: "bucket 或对象不存在",
    error_502: "GCS 后端返回错误",
    auth_needed_title: "请先登录",
    auth_needed_body: "未配置默认凭据。请上传你自己的 service account JSON 以浏览存储桶。",
    auth_needed_cta: "上传 service account",
    preview_title: "预览（前 {n} 行）",
    preview_truncated: "已截断 · 仅显示前 {n} 行",
    preview_full: "全部内容 · 共 {n} 行",
    preview_loading: "正在加载预览…",
    preview_failed: "预览加载失败：{msg}",
    preview_unsupported: "该文件类型不支持预览",
    preview_empty: "（空文件）",
  },
  en: {
    loading: "loading…",
    buckets: "Buckets",
    theme: "Theme",
    docs: "Docs",
    upload: "Upload",
    refresh: "Refresh",
    col_name: "Name",
    col_size: "Size",
    col_modified: "Last modified",
    col_type: "Type",
    empty: "No objects in this prefix.",
    drop_title: "Drop files to upload",
    drop_target_default: "to gs://…",
    drop_target_to: "to gs://{path}",
    auth_title: "Service account credentials",
    auth_help: "Drop a Google Cloud service account .json file, paste its contents, or pick from disk. Credentials are kept in memory for this session only and are never written to disk.",
    sa_drop_default: "Drop SA JSON here",
    or: "or",
    pick_file: "pick a file",
    paste_json: "Paste JSON",
    use_demo: "Use demo data",
    authenticate: "Authenticate",
    cancel: "Cancel",
    close: "Close",
    download: "Download",
    copy_uri: "Copy URI",
    uri_copied: "Copied {uri}",
    copy_failed: "Copy failed: {msg}",
    detail_bucket: "Bucket",
    detail_size: "Size",
    detail_type: "Type",
    detail_updated: "Updated",
    detail_generation: "Generation",
    detail_etag: "ETag",
    backend_demo: "Demo data",
    backend_live: "Live · GCS",
    pill_demo: "demo data · sign in",
    pill_env: "SA credentials",
    pill_needs: "Sign in required",
    pill_demo_title: "Click to upload a service account",
    pill_env_title: "Using SA credentials · click to override",
    pill_needs_title: "Not signed in — click to upload a service account",
    pill_auth_title: "Authenticated as {who} · click to switch",
    auth_pill_title: "Switch service account",
    theme_title: "Toggle theme",
    lang_title: "Switch language",
    upload_title: "Upload files (or drop them anywhere)",
    refresh_title: "Reload",
    search_placeholder: "Filter by name…",
    folders_n: "{n} folders",
    files_n: "{n} files",
    folder_type: "folder",
    just_now: "just now",
    min_ago: "{n} min ago",
    h_ago: "{n} h ago",
    d_ago: "{n} d ago",
    bytes_n: "{n} bytes",
    toast_done: "done",
    toast_failed: "upload failed",
    toast_net_err: "network error",
    pick_or_paste: "Pick a file or paste JSON first",
    signed_in_as: "Signed in as {who}",
    selected_size: "{kb} KB selected",
    download_failed: "Download failed: {msg}",
    error_generic: "Request failed",
    error_401: "Not signed in. Click the credentials pill in the sidebar to upload a service account.",
    error_403: "Permission denied — verify the service account has storage.objects.list (and friends) on this bucket.",
    error_404: "Bucket or object not found.",
    error_502: "GCS backend returned an error.",
    auth_needed_title: "Sign in required",
    auth_needed_body: "No default credentials are configured. Upload your service account JSON to browse buckets.",
    auth_needed_cta: "Upload service account",
    preview_title: "Preview (first {n} lines)",
    preview_truncated: "truncated · showing first {n} lines",
    preview_full: "full content · {n} lines",
    preview_loading: "loading preview…",
    preview_failed: "Preview failed: {msg}",
    preview_unsupported: "Preview is not supported for this file type",
    preview_empty: "(empty file)",
  },
};

const PREVIEW_LINES = 10;
const PREVIEW_EXTS = new Set([
  "csv", "tsv", "txt", "log", "json", "jsonl", "ndjson",
  "md", "markdown", "rst",
  "xml", "yaml", "yml", "html", "htm",
  "py", "js", "mjs", "ts", "css",
  "sh", "bash", "zsh", "ini", "cfg", "conf", "toml", "sql",
  "rs", "go", "java", "c", "h", "cpp", "hpp",
  "env", "properties", "gitignore", "dockerfile",
]);

function isPreviewable(item) {
  if (!item || item.is_prefix) return false;
  const ct = (item.content_type || "").split(";")[0].trim().toLowerCase();
  if (ct.startsWith("text/")) return true;
  if (["application/json", "application/x-ndjson", "application/xml",
       "application/javascript", "application/x-yaml", "application/csv",
       "application/x-sh", "application/x-shellscript"].includes(ct)) return true;
  const base = (item.name || "").split("/").pop().toLowerCase();
  const ext = base.includes(".") ? base.split(".").pop() : base;
  return PREVIEW_EXTS.has(ext);
}

let lang = localStorage.getItem("gcs-webui-lang") || "zh";

function t(key, vars) {
  let s = (I18N[lang] && I18N[lang][key]) || I18N.zh[key] || key;
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace("{" + k + "}", v);
  return s;
}

function applyStaticI18n() {
  document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
  document.title = lang === "zh" ? "GCS 浏览器" : "GCS Browser";
  for (const el of document.querySelectorAll("[data-i18n]")) {
    el.textContent = t(el.dataset.i18n);
  }
  for (const el of document.querySelectorAll("[data-i18n-placeholder]")) {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  }
  for (const el of document.querySelectorAll("[data-i18n-title]")) {
    el.title = t(el.dataset.i18nTitle);
  }
  for (const el of document.querySelectorAll("[data-i18n-aria-label]")) {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  }
  const ll = document.getElementById("lang-label");
  if (ll) ll.textContent = lang === "zh" ? "EN" : "中";
}

const state = {
  buckets: [],
  bucket: null,
  prefix: "",
  rows: [],
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
  if (diff < 60) return t("just_now");
  if (diff < 3600) return t("min_ago", { n: Math.floor(diff / 60) });
  if (diff < 86400) return t("h_ago", { n: Math.floor(diff / 3600) });
  if (diff < 86400 * 30) return t("d_ago", { n: Math.floor(diff / 86400) });
  return d.toISOString().slice(0, 10);
};

const ICONS = {
  folder: '<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-8z"/></svg>',
  file:   '<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
  download: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
  copy:     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>',
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
  if (!res.ok) {
    let detail = res.statusText;
    try { const j = await res.json(); detail = j.detail || detail; } catch {}
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

function showError(err) {
  const banner = $("#error-banner");
  const status = err && err.status;
  const key = status === 401 ? "error_401"
    : status === 403 ? "error_403"
    : status === 404 ? "error_404"
    : status === 502 ? "error_502"
    : "error_generic";
  banner.querySelector(".error-title").textContent = t(key);
  banner.querySelector(".error-detail").textContent = err && err.message ? err.message : "";
  banner.classList.remove("hidden");
}

function hideError() {
  $("#error-banner").classList.add("hidden");
}

async function loadInfo() {
  const info = await api("/api/info");
  state.info = info;
  const badge = $("#backend-badge");
  if (info.needs_credentials) {
    badge.textContent = t("pill_needs");
    badge.style.color = "#d93025";
  } else {
    badge.textContent = info.demo ? t("backend_demo") : t("backend_live");
    badge.style.color = info.demo ? "var(--text-faint)" : "var(--accent)";
  }

  const pill = $("#auth-pill");
  const text = $("#auth-text");
  if (info.needs_credentials) {
    pill.dataset.mode = "needs";
    text.textContent = t("pill_needs");
    pill.title = t("pill_needs_title");
  } else if (info.session_authenticated) {
    pill.dataset.mode = "auth";
    text.textContent = info.identity || info.project || "authenticated";
    pill.title = t("pill_auth_title", { who: info.identity || "?" });
  } else if (!info.demo) {
    pill.dataset.mode = "env";
    text.textContent = t("pill_env");
    pill.title = t("pill_env_title");
  } else {
    pill.dataset.mode = "demo";
    text.textContent = t("pill_demo");
    pill.title = t("pill_demo_title");
  }

  // Hide "use demo data" / logout button when there's no default to fall back to.
  const logoutBtn = $("#sa-logout");
  if (logoutBtn) logoutBtn.classList.toggle("hidden", !info.default_available);
}

async function loadBuckets() {
  if (state.info && state.info.needs_credentials) {
    showAuthNeeded();
    return;
  }
  hideAuthNeeded();
  try {
    state.buckets = await api("/api/buckets");
  } catch (e) {
    if (e.status === 401) { showAuthNeeded(); return; }
    showError(e);
    return;
  }
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

function showAuthNeeded() {
  $("#auth-needed").classList.remove("hidden");
  $("#bucket-list").innerHTML = "";
  $("#rows").innerHTML = "";
  $("#empty").classList.add("hidden");
  hideError();
}

function hideAuthNeeded() {
  $("#auth-needed").classList.add("hidden");
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
    hideError();
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
    if (e.status === 401) { showAuthNeeded(); return; }
    showError(e);
    renderBreadcrumbs();
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
      <div class="cell col-type">${it.is_prefix ? t("folder_type") : (it.content_type || "—")}</div>
      <div class="cell col-actions">
        ${it.is_prefix ? "" : `<button class="icon-btn" data-action="download" title="${escapeHtml(t("download"))}">${ICONS.download}</button>`}
        <button class="icon-btn" data-action="copy-uri" title="${escapeHtml(t("copy_uri"))}">${ICONS.copy}</button>
      </div>
    `;
    row.addEventListener("click", (ev) => {
      if (ev.target.closest('[data-action="download"]')) {
        ev.stopPropagation();
        downloadObject(it.name);
        return;
      }
      if (ev.target.closest('[data-action="copy-uri"]')) {
        ev.stopPropagation();
        copyGsUri(it);
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
  $("#stat-folders").textContent = t("folders_n", { n: folders.toLocaleString() });
  $("#stat-files").textContent = t("files_n", { n: files.toLocaleString() });
  $("#stat-size").textContent = fmtBytes(size);
}

function gsUri(item) {
  return `gs://${state.bucket}/${item.name}`;
}

async function copyGsUri(item) {
  const uri = gsUri(item);
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(uri);
    } else {
      const ta = document.createElement("textarea");
      ta.value = uri;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand("copy");
      ta.remove();
      if (!ok) throw new Error("execCommand copy returned false");
    }
    showToast({ name: t("uri_copied", { uri }), status: "ok", text: "" }).finish("ok");
  } catch (e) {
    showToast({ name: t("copy_failed", { msg: e.message }), status: "error", text: "" }).finish("error");
  }
}

function downloadObject(name) {
  // Navigate via a synthetic anchor so the browser follows any redirect to GCS
  // natively. Going through fetch() would cross-origin-redirect into GCS and
  // either trip CORS or save the JSON/HTML body under the wrong filename.
  const url = `/api/object/download?bucket=${encodeURIComponent(state.bucket)}&name=${encodeURIComponent(name)}`;
  const a = document.createElement("a");
  a.href = url;
  a.download = basename(name);
  document.body.appendChild(a);
  a.click();
  a.remove();
}

function openDetails(item) {
  const dlg = $("#object-dialog");
  $("#dlg-name").textContent = item.name;
  $("#dlg-bucket").textContent = state.bucket;
  $("#dlg-size").textContent = `${fmtBytes(item.size)}  (${t("bytes_n", { n: item.size?.toLocaleString() ?? "?" })})`;
  $("#dlg-type").textContent = item.content_type || "—";
  $("#dlg-updated").textContent = item.updated || "—";
  $("#dlg-generation").textContent = item.generation ?? "—";
  $("#dlg-etag").textContent = item.etag ?? "—";
  const link = $("#dlg-download");
  link.href = `/api/object/download?bucket=${encodeURIComponent(state.bucket)}&name=${encodeURIComponent(item.name)}`;
  link.setAttribute("download", basename(item.name));
  const copyBtn = $("#dlg-copy-uri");
  copyBtn.onclick = () => copyGsUri(item);
  loadPreview(item);
  if (typeof dlg.showModal === "function") dlg.showModal();
}

let _previewToken = 0;

async function loadPreview(item) {
  const section = $("#dlg-preview-section");
  const body = $("#dlg-preview");
  const meta = $("#dlg-preview-meta");
  const title = section.querySelector(".preview-title");
  title.textContent = t("preview_title", { n: PREVIEW_LINES });
  if (!isPreviewable(item)) {
    section.classList.add("hidden");
    return;
  }
  section.classList.remove("hidden");
  body.classList.remove("error");
  body.textContent = t("preview_loading");
  meta.textContent = "";
  const token = ++_previewToken;
  try {
    const data = await api("/api/object/preview", {
      bucket: state.bucket,
      name: item.name,
      lines: PREVIEW_LINES,
    });
    if (token !== _previewToken) return; // dialog was reused for another file
    if (!data.content && data.lines_shown === 0) {
      body.textContent = t("preview_empty");
    } else {
      body.textContent = data.content;
    }
    meta.textContent = data.truncated
      ? t("preview_truncated", { n: data.lines_shown })
      : t("preview_full", { n: data.lines_shown });
  } catch (e) {
    if (token !== _previewToken) return;
    body.classList.add("error");
    if (e.status === 415) {
      body.textContent = t("preview_unsupported");
      meta.textContent = "";
    } else {
      body.textContent = t("preview_failed", { msg: e.message || "" });
      meta.textContent = "";
    }
  }
}

const observer = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting && state.nextPageToken && !state.loading) {
      loadObjects(false);
    }
  }
}, { rootMargin: "200px" });

function setupSearch() {
  const input = $("#search-input");
  let tm;
  input.addEventListener("input", () => {
    clearTimeout(tm);
    tm = setTimeout(() => {
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

function setupLanguageToggle() {
  $("#lang-toggle").addEventListener("click", async () => {
    lang = lang === "zh" ? "en" : "zh";
    localStorage.setItem("gcs-webui-lang", lang);
    applyStaticI18n();
    await loadInfo();
    renderStats();
    $("#rows").innerHTML = "";
    appendRows(state.rows);
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
        toast.update(100, t("toast_done"));
        toast.finish("ok");
      } else {
        let msg = t("toast_failed");
        try { msg = JSON.parse(xhr.responseText).detail || msg; } catch {}
        toast.update(0, msg);
        toast.finish("error");
      }
      onAllDone();
    });
    xhr.addEventListener("error", () => {
      pending--;
      toast.update(0, t("toast_net_err"));
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
      label.textContent = t("drop_target_to", { path: `${state.bucket}/${state.prefix}` });
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
    drop.querySelector("div").textContent = t("sa_drop_default");
  };

  const setFile = (file) => {
    pendingFile = file;
    drop.querySelector("div").textContent = file.name;
    status.textContent = t("selected_size", { kb: (file.size / 1024).toFixed(1) });
    status.classList.remove("error");
  };

  $("#auth-pill").addEventListener("click", () => {
    reset();
    if (typeof dlg.showModal === "function") dlg.showModal();
  });

  ["dragenter", "dragover"].forEach((evt) =>
    drop.addEventListener(evt, (e) => { e.preventDefault(); drop.classList.add("dragover"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    drop.addEventListener(evt, (e) => { e.preventDefault(); drop.classList.remove("dragover"); })
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
      status.textContent = t("pick_or_paste");
      status.classList.add("error");
      return;
    }
    submit.disabled = true;
    try {
      const r = await fetch("/api/auth/sa", { method: "POST", body, headers });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
      status.textContent = t("signed_in_as", { who: data.identity });
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
  applyStaticI18n();
  setupSearch();
  setupTheme();
  setupLanguageToggle();
  setupDragAndDrop();
  setupUploadButton();
  setupAuthDialog();
  $("#refresh").addEventListener("click", () => loadObjects(true));
  $("#error-dismiss").addEventListener("click", hideError);
  $("#auth-needed-btn").addEventListener("click", () => $("#auth-pill").click());
  observer.observe($("#sentinel"));
  await loadInfo();
  await loadBuckets();
}

init();
