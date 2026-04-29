from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, List

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

PROFILE_SCHEMA = {
    "name": "mempalace_profile",
    "description": (
        "Retrieve all stored memories about the user — preferences, facts, "
        "project context. Use at conversation start."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

SEARCH_SCHEMA = {
    "name": "mempalace_search",
    "description": (
        "Search memories by meaning."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."},
        },
        "required": ["query"],
    },
}

MINE_SCHEMA = {
    "name": "mempalace_mine",
    "description": (
        "Store a durable fact about the user. Stored verbatim."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "The fact to store."},
        },
        "required": ["text"],
    },
}

class MemPalaceMemoryProvider(MemoryProvider):
    """MemPalace memory provider."""

    def __init__(self):
        self._user_id = "hermes-user"
        self._agent_id = "hermes"
        
        self._prefetch_result = ""
        self._prefetch_lock = threading.Lock()
        self._prefetch_thread = None
        self._sync_thread = None
        self._workspace = ""
        self._hermes_home = ""

    @property
    def name(self) -> str:
        return "mempalace"

    def is_available(self) -> bool:
        try:
            import mempalace
            import chromadb
            return True
        except ImportError:
            return False

    def initialize(self, session_id: str, **kwargs) -> None:
        self._user_id = kwargs.get("user_id") or "hermes-user"
        self._workspace = kwargs.get("agent_workspace", "")
        self._hermes_home = kwargs.get("hermes_home", "")
        
    def _get_db_dir(self):
        try:
            from hermes_constants import get_hermes_home
            base_dir = get_hermes_home()
        except ImportError:
            base_dir = self._hermes_home if self._hermes_home else os.path.expanduser("~/.hermes")
        return os.path.join(str(base_dir), "mempalace_db")

    def system_prompt_block(self) -> str:
        return (
            "# MemPalace Memory\n"
            f"Active. User: {self._user_id}.\n"
            "Use mempalace_search to find memories, mempalace_mine to store facts."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        if self._prefetch_thread and self._prefetch_thread.is_alive():
            self._prefetch_thread.join(timeout=3.0)
        with self._prefetch_lock:
            result = self._prefetch_result
            self._prefetch_result = ""
        if not result:
            return ""
        return f"## MemPalace Memory\n{result}"

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        def _run():
            try:
                from mempalace.searcher import search_memories
                db_dir = self._get_db_dir()
                os.makedirs(db_dir, exist_ok=True)
                res = search_memories(query, db_dir, wing=self._user_id, n_results=5)
                results = res.get('results', [])
                if results:
                    lines = [r['text'] for r in results if 'text' in r]
                    with self._prefetch_lock:
                        self._prefetch_result = "\n".join(f"- {l}" for l in lines)
            except Exception as e:
                logger.debug(f"MemPalace prefetch failed: {e}")

        self._prefetch_thread = threading.Thread(target=_run, daemon=True, name="mempalace-prefetch")
        self._prefetch_thread.start()

    def sync_turn(self, user_content: str, assistant_content: str, *, session_id: str = "") -> None:
        def _sync():
            try:
                import time
                from mempalace.miner import add_drawer
                from mempalace.palace import get_collection
                
                db_dir = self._get_db_dir()
                os.makedirs(db_dir, exist_ok=True)
                col = get_collection(db_dir)
                
                text_to_mine = f"User: {user_content}\nAssistant: {assistant_content}"
                room = f"session_{session_id}" if session_id else "default_session"
                wing = self._user_id
                source = f"turn_{int(time.time())}"
                
                add_drawer(col, wing, room, text_to_mine, source, 0, self._agent_id)
            except Exception as e:
                logger.warning(f"MemPalace sync failed: {e}")

        if self._sync_thread and self._sync_thread.is_alive():
            self._sync_thread.join(timeout=5.0)

        self._sync_thread = threading.Thread(target=_sync, daemon=True, name="mempalace-sync")
        self._sync_thread.start()

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return [PROFILE_SCHEMA, SEARCH_SCHEMA, MINE_SCHEMA]

    def handle_tool_call(self, tool_name: str, args: dict, **kwargs) -> str:
        try:
            db_dir = self._get_db_dir()
            os.makedirs(db_dir, exist_ok=True)
            
            if tool_name == "mempalace_profile":
                try:
                    from mempalace.searcher import search_memories
                    res = search_memories("", db_dir, wing=self._user_id, n_results=50)
                    results = res.get('results', [])
                    if not results:
                        return json.dumps({"result": "No memories stored yet."})
                    lines = [r['text'] for r in results if 'text' in r]
                    return json.dumps({"result": "\n".join(lines), "count": len(lines)})
                except Exception as e:
                    return tool_error(f"Failed to fetch profile: {e}")

            elif tool_name == "mempalace_search":
                query = args.get("query", "")
                if not query:
                    return tool_error("Missing required parameter: query")
                try:
                    from mempalace.searcher import search_memories
                    res = search_memories(query, db_dir, wing=self._user_id, n_results=10)
                    results = res.get('results', [])
                    if not results:
                        return json.dumps({"result": "No relevant memories found."})
                    items = [{"memory": r['text'], "score": r.get('similarity', 0)} for r in results if 'text' in r]
                    return json.dumps({"results": items, "count": len(items)})
                except Exception as e:
                    return tool_error(f"Search failed: {e}")

            elif tool_name == "mempalace_mine":
                text = args.get("text", "")
                if not text:
                    return tool_error("Missing required parameter: text")
                try:
                    import time
                    from mempalace.miner import add_drawer
                    from mempalace.palace import get_collection
                    col = get_collection(db_dir)
                    add_drawer(col, self._user_id, "manual_mine", text, f"manual_{int(time.time())}", 0, self._agent_id)
                    return json.dumps({"result": "Fact stored."})
                except Exception as e:
                    return tool_error(f"Failed to store: {e}")

            return tool_error(f"Unknown tool: {tool_name}")
        except Exception as e:
            return tool_error(str(e))

    def shutdown(self) -> None:
        for t in (self._prefetch_thread, self._sync_thread):
            if t and t.is_alive():
                t.join(timeout=5.0)

def register(ctx) -> None:
    """Register MemPalace as a memory provider plugin."""
    ctx.register_memory_provider(MemPalaceMemoryProvider())
