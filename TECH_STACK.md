# 技术栈与决策

本文档记录 `gcs-webui` 的技术选择与背后的取舍。整体目标是 **最小依赖、低资源占用、易部署、面向 Python/Java 开发者的现代化体验**。

## 总览

| 层 | 选型 | 备选 | 选择原因 |
| --- | --- | --- | --- |
| 后端框架 | **FastAPI** | Flask, Starlette, aiohttp | 异步 IO（GCS 列举可并发）、自带类型校验、依赖少（pydantic + starlette）、镜像体积小 |
| ASGI 服务器 | **Uvicorn** | Hypercorn, Gunicorn | 与 FastAPI 配套、单一进程内存占用低 |
| GCS SDK | **google-cloud-storage** | REST 直接调用 | 官方支持、自动处理签名 / 重试 / 分页；体积可接受 |
| 前端 | **原生 HTML + CSS + Vanilla JS（ES Modules）** | React/Vue/Svelte/Alpine | 零构建步骤、镜像小、加载快、长期维护成本低 |
| 列表性能 | **服务端分页（`pageToken`）+ 客户端无限滚动 (`IntersectionObserver`)** | 客户端虚拟列表 | 直接利用 GCS 原生分页，避免一次性下载 1000+ 元数据；浏览器只持有可视范围内 DOM |
| 样式 | **手写 CSS**（CSS variables + grid/flex） | Tailwind CDN, Bootstrap | 无运行时下载、定制化高、便于实现 dark/light 设计 |
| 图标 | **Inline SVG** | 图标字体 | 单文件、无外部请求、可着色 |
| 容器 | **多阶段 Dockerfile，基于 `python:3.12-slim`** | distroless, alpine | 体积可控（< 200 MB）、`google-cloud-storage` 在 alpine 上需要编译 |
| 测试 | **Playwright (Python) + Pytest** | Selenium, Cypress | 原生支持 Chromium 截图、API 简洁、与目标"兼容 Chrome"对齐 |

## 关键设计

### 1. 认证 —— Service Account JSON

支持三种加载方式，按优先级：

1. **运行时切换**：用户点击右上角的"凭据徽章"，可拖拽 / 选择 / 粘贴 SA JSON，本浏览器会话立即换用该凭据。
2. 环境变量 `GOOGLE_APPLICATION_CREDENTIALS` 指向已挂载的 JSON（默认凭据 / 服务级别）。
3. 环境变量 `GCS_SA_JSON` 直接保存完整 JSON 字符串（适合 K8s Secret）。

#### 多租户隔离

* 每个浏览器分配一个 `gcs_webui_sid` cookie（`HttpOnly` + `SameSite=Lax`，24 小时有效）。
* 服务端 `SessionRegistry`（`app/sessions.py`）把 sid 映射到一个 `Session`，里面持有该会话独享的 `GcsStorage`（含独立的 `google.cloud.storage.Client`）。
* 默认上限 64 个会话，闲置 24h 自动清理；超出走 LRU 淘汰。
* 凭据 **只在内存中**存在，永远不落盘，不通过 API 回显，注销 (`POST /api/auth/logout`) 即清空。
* 未上传 SA 的会话回退到启动时配置的默认 storage（env 凭据或 demo）；不同会话之间彼此完全独立——A 上传 SA 不会影响 B。

### 2. 浏览体验

* **抽象层 `Storage`**：定义 `list_buckets / list_objects / get_metadata / read_object` 四个方法。生产用 `GcsStorage`，测试用 `FakeStorage`。同一接口让 UI 完全不感知后端是真是假，方便演示与单测。
* **目录感**：使用 `delimiter="/"` 让 GCS 返回 prefix（伪文件夹）；前端把它们和 blob 合并展示，并用面包屑维护当前路径。
* **分页**：每页 200 项，向下滚动到哨兵元素时自动请求下一页；GCS 的 `nextPageToken` 在前端作为黑盒透传。
* **搜索**：UI 上的搜索框对当前已加载条目做客户端过滤（即时反馈），同时把内容作为 `prefix` 选项推到下一次请求（对大目录有效）。

### 3. 资源占用

* 单个 uvicorn worker，内存稳态 ~60 MB。
* 前端总资源 < 25 KB（gzip 后）：`index.html` ~3KB / `styles.css` ~7KB / `app.js` ~12KB。
* 没有 SPA 路由 / 状态库，浏览器内存随分页保持低位。

### 4. 部署

* `docker compose up`：单容器，挂载 SA JSON 即可。
* `Dockerfile` 不含构建工具链，运行用户为非 root，端口 8080。
* 健康检查路径 `/healthz`。

### 5. 浏览器兼容

目标 Chrome（含 Chromium 衍生）。使用的特性：CSS Grid、`IntersectionObserver`、`fetch`、ES2020 模块——全部在 Chrome 90+ 原生可用。

### 6. 上传

* `POST /api/object/upload`（multipart/form-data，字段 `bucket`、`prefix`、`files[]`）。
* 浏览器端用 `XMLHttpRequest` 监听 `progress` 事件，显示每个文件的进度 toast；完成后自动刷新当前列表。
* 拖拽：监听 `window` 的 `dragenter / dragover / drop`，整页覆盖半透明指示层；文件落点区域不限，目标 = 当前 bucket + prefix。
* 删除 / 重命名仍未实现（保持只读以外的最小写面）。

## 不做的事

* **不做删除 / 重命名**：高风险且需要更多 UI 状态；后续可作为 opt-in 模块加入。
* **不做用户系统 / RBAC**：依赖 service account 本身的权限粒度。
* **不做服务端模板**：前端完全静态，后端只暴露 JSON API。
