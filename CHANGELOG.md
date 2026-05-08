# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2026-05-08
### Fixed
- **ChromaDB Rust Bindings Error**: Fixed an issue where concurrent reads/writes could crash the underlying Rust engine (`'RustBindingsAPI' object has no attribute 'bindings'`).
- **Data Drift Auto-Healing**: Added automatic detection and quarantine of stale HNSW index segments that drift from the SQLite metadata database, preventing segmentation faults on initialization.
- **Thread Safety**: Introduced a global database lock (`self._db_lock`) ensuring that all ChromaDB access within the `prefetch` and `sync_turn` threads is fully thread-safe.

## [1.0.0] - Initial Release
- Initial implementation of the MemPalace In-process memory plugin.
- Added `mempalace_profile`, `mempalace_search`, and `mempalace_mine` tool schemas.
