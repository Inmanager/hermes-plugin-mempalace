# Hermes Agent MemPalace Memory Plugin
[中文版](README_zh.md) | English

## What is this?
This is a **Memory Plugin** for [Hermes Agent](https://github.com/NousResearch/hermes-agent). It gives Hermes a "long-term memory" so it can remember what you talked about across different days and sessions.

## What is the relationship with MemPalace?
[MemPalace](https://github.com/MemPalace/mempalace) is an excellent, standalone, local AI memory database. Think of it as a highly organized brain or filing cabinet for AI.

This plugin is the **bridge** that connects Hermes Agent to MemPalace. 
- MemPalace does the heavy lifting: storing facts, embedding text, and searching for context.
- This Plugin tells Hermes *how* to talk to MemPalace, so Hermes automatically saves your conversations and recalls past facts before replying to you.

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
If you already installed a previous version and want to update to the latest release (e.g., v1.1.0), just run this command in your terminal:
```bash
cd ~/.hermes/plugins/mempalace && git pull origin main
```
Restart your Hermes agent, and you will be on the latest version!
