# Hermes Agent MemPalace Memory Plugin
[中文版](README_zh.md) | English

## What is this?
This is a **Memory Plugin** for [Hermes Agent](https://github.com/NousResearch/hermes-agent). It gives Hermes a "long-term memory" so it can remember what you talked about across different days and sessions.

## What is the relationship with MemPalace?
[MemPalace](https://github.com/MemPalace/mempalace) is an excellent, standalone, local AI memory database. Think of it as a highly organized brain or filing cabinet for AI.

Objectively speaking, MemPalace natively provides a standard MCP (Model Context Protocol) interface, which means it works "out-of-the-box" with any MCP-compatible client.

**Since it works out of the box, why build a dedicated plugin?**

While invoking MemPalace via the MCP protocol is perfectly viable, it introduces a significant architectural pain point: **high Token consumption and extra request latency**. In a traditional MCP setup, memory storage and retrieval are exposed to the LLM as "Tools". The system has to repeatedly pass lengthy tool definitions, invocation steps, and retrieval results back and forth as context to the LLM. For high-frequency memory management operations, this not only wastes your precious Token quota but also slows down the model's response time.

To solve this, this plugin uses a far more optimized integration approach:
- **Native Pipeline Integration**: The plugin bypasses the generic MCP protocol layer. Instead, it uses internal APIs to plug MemPalace's core capabilities directly and seamlessly into Hermes Agent's low-level memory processing pipeline.
- **Silent Context Injection**: MemPalace still handles the heavy lifting like text vectorization and similarity search. However, this plugin silently preloads relevant memories into the system context in the background *before* the LLM generates a reply, and automatically archives the conversation asynchronously afterwards.
- **Ultimate Performance and Cost Optimization**: The LLM no longer needs to frequently "proactively call a tool" to recall the past. This grants Hermes long-term memory with zero extra interaction turns, keeping Token overhead and latency to an absolute minimum.

## Why do I need this? (Use Cases)
By default, when you start a new chat with Hermes, it forgets everything from previous chats. 
With this plugin enabled:
- **It Remembers You**: Tell Hermes your name or preferences once, and it remembers forever.
- **Cross-Session Recall**: If you ask "What were we working on yesterday?", Hermes can search its MemPalace brain and tell you.
- **Automatic Background Sync**: You don't have to do anything. Every time Hermes answers you, it quietly files the conversation into MemPalace.
- **Context Prefetching**: Before Hermes even starts typing a reply, this plugin secretly searches past memories for relevant context and injects them into Hermes's prompt. 
- **100% Local & Free**: It runs entirely on your machine. No APIs, no subscriptions, no data sent to the cloud.

## Installation for Beginners

### Step 1: Install the Engine (MemPalace)
First, we need to install the MemPalace engine into Hermes's Python environment.
```bash
~/.hermes/hermes-agent/venv/bin/pip install mempalace chromadb orjson
```

### Step 2: Download the Plugin
Download this plugin into Hermes's plugin directory:
```bash
git clone https://github.com/Inmanager/hermes-plugin-mempalace ~/.hermes/plugins/mempalace
```

### Step 3: Turn it On
Tell Hermes to use this new memory plugin.
Enable the plugin:
```bash
hermes plugins enable mempalace
```

Edit your Hermes configuration file (`~/.hermes/config.yaml`) to set it as the default memory provider. Add or update the `memory` section:
```yaml
memory:
  provider: mempalace
```

### Step 4: Verify
Run this command to check if it's working:
```bash
hermes memory status
```
If you see `mempalace` listed as the active provider, you're all set!

## How to Update
If you already installed a previous version and want to update to the latest release (e.g., v1.3.0), just run this command in your terminal:
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```
Restart your Hermes agent, and you will be on the latest version!

## What's New in v1.3.0
- Serializes cross-process MemPalace access with a file lock so multiple Hermes processes are less likely to corrupt the same ChromaDB index.
- Adds one-shot automatic index repair when the plugin detects a classic corrupt-index signature such as `Error finding id`.

## What's New in v1.2.0
- Automatically reconnects when a rebuilt MemPalace collection gets a new internal ID, preventing `Collection [...] does not exist` errors after index repair/rebuild.
- Falls back to direct stored-memory reads when semantic search temporarily fails, avoiding false `No memories stored yet.` reports when the database still contains data.

## Troubleshooting

### Error: `Collection [...] does not exist`
This usually means MemPalace rebuilt its internal ChromaDB collection, but Hermes was still holding a stale cached handle.

What to do:
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```
Then restart Hermes.

Success sign:
- Hermes starts normally
- Memory search works again instead of raising the collection-ID error

### Error: `No memories stored yet.`
This message can be misleading. In some failure modes the vector search path is broken while the underlying SQLite data is still present.

What to do:
- Update to the latest plugin version
- Restart Hermes
- Try a direct memory search again

Success sign:
- Hermes can show older stored content again instead of reporting an empty memory state

### Error: `Error finding id`
This usually indicates a damaged or drifted ChromaDB HNSW index, often after repeated concurrent access from multiple Hermes processes.

What to do:
1. Update the plugin to the latest version
2. Restart Hermes
3. If the problem still appears, rebuild the MemPalace index manually:

```bash
python3 -m mempalace.repair rebuild --palace ~/.hermes/mempalace_db
```

Success sign:
- Semantic search returns real memories again
- Hermes no longer behaves like it "forgot everything"
