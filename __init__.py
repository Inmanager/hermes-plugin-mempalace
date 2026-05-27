from __future__ import annotations

import json
import logging
import os
import re
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
        self._db_lock = threading.Lock()
        self._collection_cache = None

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

    def _get_collection_safe(self, db_dir):
        from mempalace.palace import get_collection
        if self._collection_cache is not None:
            try:
                self._collection_cache.count()
                return self._collection_cache
            except Exception as exc:
                if self._is_stale_collection_error(exc):
                    logger.warning("MemPalace cached collection went stale, reconnecting: %s", exc)
                    self._collection_cache = None
                else:
                    raise
        try:
            from mempalace.backends.chroma import quarantine_stale_hnsw, _fix_blob_seq_ids
            _fix_blob_seq_ids(db_dir)
            quarantine_stale_hnsw(db_dir, stale_seconds=3600.0)
        except ImportError:
            pass  # Older mempalace version without auto-heal
            
        self._collection_cache = get_collection(db_dir)
        return self._collection_cache

    @staticmethod
    def _is_stale_collection_error(exc) -> bool:
        msg = str(exc)
        needles = (
            "does not exist",
            "Error getting collection",
            "Error finding id",
            "Collection [",
        )
        return any(needle in msg for needle in needles)

    def _clear_collection_cache(self):
        self._collection_cache = None

    def _retry_on_stale_collection(self, fn):
        try:
            return fn()
        except Exception as exc:
            if not self._is_stale_collection_error(exc):
                raise
            logger.warning("MemPalace stale collection detected, retrying with fresh handle: %s", exc)
            self._clear_collection_cache()
            return fn()

    def _list_memories(self, db_dir, *, room=None, limit=50):
        def _run():
            col = self._get_collection_safe(db_dir)
            where = {"wing": self._user_id}
            if room:
                where["room"] = room
            return col.get(where=where, include=["documents", "metadatas"], limit=limit)

        return self._retry_on_stale_collection(_run)

    def _fallback_search(self, db_dir, query: str, *, limit=10):
        batch = self._list_memories(db_dir, limit=500)
        docs = batch.documents or []
        metas = batch.metadatas or []
        if not docs:
            return {"results": []}

        tokens = [t for t in re.findall(r"\w+", (query or "").lower()) if t]
        scored = []
        for doc, meta in zip(docs, metas):
            text = doc or ""
            hay = text.lower()
            score = 0
            if not tokens:
                score = 1
            else:
                score = sum(hay.count(tok) for tok in tokens)
                if query and query.lower() in hay:
                    score += max(2, len(tokens))
            if score <= 0:
                continue
            scored.append(
                {
                    "text": text,
                    "similarity": round(min(0.99, 0.3 + 0.1 * score), 3),
                    "metadata": meta or {},
                    "_score": score,
                }
            )

        scored.sort(key=lambda item: item["_score"], reverse=True)
        for item in scored:
            item.pop("_score", None)
        return {"results": scored[:limit]}

    def _search_memories_safe(self, db_dir, query: str, *, limit=10):
        from mempalace.searcher import search_memories

        try:
            def _run():
                with self._db_lock:
                    self._get_collection_safe(db_dir)
                    return search_memories(query, db_dir, wing=self._user_id, n_results=limit)

            res = self._retry_on_stale_collection(_run)
        except Exception as exc:
            logger.warning("MemPalace semantic search failed, using fallback grep: %s", exc)
            return self._fallback_search(db_dir, query, limit=limit)

        if isinstance(res, dict) and res.get("error"):
            logger.warning("MemPalace semantic search returned error, using fallback grep: %s", res["error"])
            return self._fallback_search(db_dir, query, limit=limit)
        return res

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
                db_dir = self._get_db_dir()
                os.makedirs(db_dir, exist_ok=True)
                res = self._search_memories_safe(db_dir, query, limit=5)
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
                
                db_dir = self._get_db_dir()
                os.makedirs(db_dir, exist_ok=True)
                
                text_to_mine = f"User: {user_content}\nAssistant: {assistant_content}"
                room = f"session_{session_id}" if session_id else "default_session"
                wing = self._user_id
                source = f"turn_{int(time.time())}"
                
                with self._db_lock:
                    def _run():
                        col = self._get_collection_safe(db_dir)
                        add_drawer(col, wing, room, text_to_mine, source, 0, self._agent_id)
                    self._retry_on_stale_collection(_run)
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
                    batch = self._list_memories(db_dir, limit=50)
                    docs = batch.documents or []
                    metas = batch.metadatas or []
                    ordered = []
                    for doc, meta in zip(docs, metas):
                        ordered.append((meta.get("filed_at", ""), doc))
                    ordered.sort(key=lambda item: item[0], reverse=True)
                    results = [doc for _, doc in ordered if doc]
                    if not results:
                        return json.dumps({"result": "No memories stored yet."})
                    return json.dumps({"result": "\n".join(results), "count": len(results)})
                except Exception as e:
                    return tool_error(f"Failed to fetch profile: {e}")

            elif tool_name == "mempalace_search":
                query = args.get("query", "")
                if not query:
                    return tool_error("Missing required parameter: query")
                try:
                    res = self._search_memories_safe(db_dir, query, limit=10)
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
                    with self._db_lock:
                        def _run():
                            col = self._get_collection_safe(db_dir)
                            add_drawer(col, self._user_id, "manual_mine", text, f"manual_{int(time.time())}", 0, self._agent_id)
                        self._retry_on_stale_collection(_run)
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
