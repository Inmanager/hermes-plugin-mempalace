# Hermes Agent MemPalace Memory Plugin

A local-first, zero-API memory provider plugin for [Hermes Agent](https://github.com/NousResearch/hermes-agent), backed by [MemPalace](https://github.com/MemPalace/mempalace).

MemPalace provides highly efficient semantic retrieval and offline knowledge graph capabilities, enabling Hermes to recall past conversations and durable facts without blowing up the context window.

## Features

- **Automatic Sync**: Quietly saves completed turns to local SQLite/ChromaDB.
- **Context Prefetching**: Uses BM25 + Vector hybrid search to pull relevant historical turns into the active context before Hermes replies.
- **Zero-API Cost**: Entirely local embedding generation (defaults to all-MiniLM-L6-v2) and retrieval.
- **Fault-isolated**: Fully wrapped in try/except blocks; if the memory backend fails, it falls back gracefully without crashing your agent session.

## Installation

1. Ensure the required backend package is installed in Hermes's virtual environment:
   ```bash
   ~/.hermes/hermes-agent/venv/bin/pip install mempalace chromadb orjson
   ```

2. Clone or copy this repository into your Hermes plugins directory:
   ```bash
   cp -r hermes-mempalace-plugin ~/.hermes/plugins/mempalace
   ```

3. Enable the plugin in your `~/.hermes/config.yaml`:
   ```yaml
   plugins:
     enabled:
       - mempalace

   memory:
     provider: mempalace
   ```

4. Verify installation:
   ```bash
   hermes memory status
   ```
   You should see `mempalace` listed as the active provider.

## How it Works

The plugin implements the `MemoryProvider` ABC from Hermes Core. 

- **Storage Path**: Memories are stored locally at `~/.hermes/mempalace_db` (or inside the active profile directory if configured).
- **Tools Injected**:
  - `mempalace_mine`: For explicit, durable fact memorization.
  - `mempalace_search`: For explicit historical querying.
  - `mempalace_profile`: For reading all facts stored globally.
