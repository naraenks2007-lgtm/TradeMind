import os
import sqlite3
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings


class ConversationStore:
    """Durable, session-scoped conversation storage backed by SQLite."""

    def __init__(self) -> None:
        self.db_path = Path(os.getenv("TRADEMIND_CHAT_DB_PATH", str(Path(settings.DATA_DIR) / "conversations.sqlite3")))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    instrument TEXT,
                    current_price REAL,
                    data_source TEXT,
                    data_timestamp TEXT,
                    recalled_memories TEXT,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session_updated ON conversations(session_id, updated_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON conversation_messages(conversation_id, created_at)")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _conversation(row: sqlite3.Row) -> Dict[str, Any]:
        return dict(row)

    def list_conversations(self, session_id: str) -> List[Dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT c.*, (SELECT COUNT(*) FROM conversation_messages m WHERE m.conversation_id=c.id) AS message_count "
                "FROM conversations c WHERE session_id=? ORDER BY updated_at DESC",
                (session_id,)
            ).fetchall()
        return [dict(row) for row in rows]

    def create_conversation(self, session_id: str, instrument: str, title: str = "New conversation") -> Dict[str, Any]:
        now = self._now()
        conversation_id = str(uuid.uuid4())
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO conversations(id, session_id, title, instrument, created_at, updated_at) VALUES(?,?,?,?,?,?)",
                (conversation_id, session_id, title[:80], instrument, now, now)
            )
            row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
        return dict(row)

    def get_conversation(self, session_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM conversations WHERE id=? AND session_id=?",
                (conversation_id, session_id)
            ).fetchone()
            if not row:
                return None
            messages = conn.execute(
                "SELECT id, role, content, created_at, instrument, current_price, data_source, data_timestamp, recalled_memories "
                "FROM conversation_messages WHERE conversation_id=? ORDER BY created_at ASC",
                (conversation_id,)
            ).fetchall()
        result = dict(row)
        result["messages"] = []
        import json
        for message in messages:
            item = dict(message)
            item["recalled_memories"] = json.loads(item["recalled_memories"] or "[]")
            result["messages"].append(item)
        return result

    def append_exchange(self, session_id: str, conversation_id: str, instrument: str, user_text: str,
                        answer: str, response: Any) -> Optional[Dict[str, Any]]:
        import json
        now = self._now()
        with self._connection() as conn:
            conversation = conn.execute(
                "SELECT id, title FROM conversations WHERE id=? AND session_id=?",
                (conversation_id, session_id)
            ).fetchone()
            if not conversation:
                return None
            title = conversation["title"]
            if title == "New conversation":
                title = " ".join(user_text.strip().split())[:64]
                if len(user_text.strip()) > 64:
                    title = title.rstrip() + "…"
            conn.execute(
                "INSERT INTO conversation_messages(id, conversation_id, role, content, created_at, instrument) VALUES(?,?,?,?,?,?)",
                (str(uuid.uuid4()), conversation_id, "user", user_text, now, instrument)
            )
            conn.execute(
                """INSERT INTO conversation_messages
                (id, conversation_id, role, content, created_at, instrument, current_price, data_source, data_timestamp, recalled_memories)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), conversation_id, "assistant", answer, self._now(), response.instrument,
                 response.current_price, response.data_source, response.data_timestamp,
                 json.dumps(response.recalled_memories or []))
            )
            conn.execute(
                "UPDATE conversations SET title=?, instrument=?, updated_at=? WHERE id=?",
                (title, instrument, self._now(), conversation_id)
            )
        return self.get_conversation(session_id, conversation_id)

    def delete_conversation(self, session_id: str, conversation_id: str) -> bool:
        with self._connection() as conn:
            cursor = conn.execute("DELETE FROM conversations WHERE id=? AND session_id=?", (conversation_id, session_id))
            return cursor.rowcount > 0


conversation_store = ConversationStore()
