# Changelog

All notable changes to this project will be documented in this file.

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
