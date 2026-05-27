# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-05-27

### 🇺🇸 English

**Fixed**
- **Rebuilt Collection Auto-Reconnect**: Fixed a failure mode where MemPalace index rebuilds changed the internal ChromaDB collection ID and the plugin kept using a stale cached handle, causing `Collection [...] does not exist`.
- **Graceful Search Degradation**: Fixed a misleading empty-state path where semantic search failures could surface as `No memories stored yet.` even though the database still contained memories.
- **Safer Read/Write Retry Path**: Added stale-collection retry handling for profile reads, semantic search, background prefetch, and memory writes.

**Changed**
- Added a lightweight fallback search path based on stored drawer content so the plugin can still surface useful memory when vector search is temporarily unhealthy.

**How to update:**
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```

---

### 🇨🇳 中文版

**修复 (Fixed)**
- **重建后的 Collection 自动重连**: 修复了 MemPalace 索引重建后内部 ChromaDB collection ID 变化，但插件仍继续使用旧缓存句柄，最终报出 `Collection [...] does not exist` 的问题。
- **搜索异常时不再误报空记忆**: 修复了语义搜索失败时被错误显示为 `No memories stored yet.` 的问题。即使数据库里实际上还有记忆，也不会再被误判成“空状态”。
- **更稳的读写重试路径**: 为 profile 读取、语义搜索、后台 prefetch、记忆写入增加了 stale collection 自动重试。

**变更 (Changed)**
- 新增基于已存 drawer 文本的轻量 fallback 检索路径，在向量搜索临时异常时，插件仍能尽量返回可用记忆。

**如何更新 (How to update):**
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```

## [1.1.0] - 2026-05-08

### 🇺🇸 English

**Fixed**
- **ChromaDB Rust Bindings Error**: Fixed an issue where concurrent reads/writes could crash the underlying Rust engine (`'RustBindingsAPI' object has no attribute 'bindings'`).
- **Data Drift Auto-Healing**: Added automatic detection and quarantine of stale HNSW index segments that drift from the SQLite metadata database, preventing segmentation faults on initialization.
- **Thread Safety**: Introduced a global database lock (`self._db_lock`) ensuring that all ChromaDB access within the `prefetch` and `sync_turn` threads is fully thread-safe.

**How to update:**
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```

---

### 🇨🇳 中文版

**修复 (Fixed)**
- **ChromaDB Rust 引擎报错**: 修复了由于并发读写可能导致底层 Rust 引擎崩溃的问题 (`'RustBindingsAPI' object has no attribute 'bindings'`)。
- **数据漂移自动修复 (Auto-Healing)**: 增加了针对过期 HNSW 索引片段的自动检测与隔离机制。当索引与 SQLite 元数据发生漂移时自动修复，防止初始化时出现段错误 (Segmentation Fault)。
- **线程安全 (Thread Safety)**: 引入了全局数据库锁 (`self._db_lock`)，确保在 `prefetch` 和 `sync_turn` 线程中所有的 ChromaDB 数据库访问都是绝对线程安全的。

**如何更新 (How to update):**
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```

## [1.0.0] - Initial Release
- Initial implementation of the MemPalace In-process memory plugin.
- Added `mempalace_profile`, `mempalace_search`, and `mempalace_mine` tool schemas.
