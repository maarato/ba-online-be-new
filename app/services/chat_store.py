import os
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime, timezone
import json


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Ruta por defecto del archivo SQLite: ./data/chat.sqlite3 (relativa al root del proyecto)
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_DEFAULT_DB_PATH = os.path.join(_ROOT_DIR, "data", "chat.sqlite3")
_DB_PATH = os.getenv("CHAT_DB_PATH", _DEFAULT_DB_PATH)


def _ensure_dir_exists(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Inicializa el archivo de base de datos y tablas si no existen."""
    _ensure_dir_exists(_DB_PATH)
    with _connect() as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            PRAGMA journal_mode=WAL;

            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS apolo_state (
                session_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


def ensure_session(session_id: str) -> Dict[str, str]:
    """Crea la sesión si no existe y retorna sus datos."""
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO sessions (session_id, created_at) VALUES (?, ?)",
            (session_id, _iso_now()),
        )
        conn.commit()
        cur.execute("SELECT session_id, created_at FROM sessions WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
        return {"session_id": row["session_id"], "created_at": row["created_at"]}


def add_message(session_id: str, role: str, content: str) -> None:
    """Agrega un mensaje al historial de una sesión."""
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, _iso_now()),
        )
        conn.commit()


def get_messages(session_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
    """Obtiene el historial de mensajes de una sesión.

    Si se especifica `limit`, retorna los últimos N mensajes en orden cronológico.
    """
    with _connect() as conn:
        cur = conn.cursor()
        if limit is None:
            cur.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,),
            )
            rows = cur.fetchall()
        else:
            # Obtenemos últimos N (desc) y luego invertimos para orden ascendente
            cur.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            )
            rows = list(reversed(cur.fetchall()))

    return [{"role": r["role"], "content": r["content"]} for r in rows]


def get_apolo_state(session_id: str) -> Optional[Dict]:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT state_json FROM apolo_state WHERE session_id = ?", (session_id,))
        row = cur.fetchone()
        if not row:
            return None
        try:
            return json.loads(row["state_json"])  # type: ignore
        except Exception:
            return None


def set_apolo_state(session_id: str, state: Dict) -> None:
    payload = json.dumps(state, ensure_ascii=False)
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO apolo_state (session_id, state_json, updated_at) VALUES (?, ?, ?)\n             ON CONFLICT(session_id) DO UPDATE SET state_json=excluded.state_json, updated_at=excluded.updated_at",
            (session_id, payload, _iso_now()),
        )
        conn.commit()


def delete_apolo_state(session_id: str) -> int:
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM apolo_state WHERE session_id = ?", (session_id,))
        conn.commit()
        return cur.rowcount


def reset_session(session_id: str) -> Dict[str, int | bool]:
    """Elimina el historial de conversación y la fila de sesión.

    Retorna dict con:
      - had_conversation: bool (si existían mensajes)
      - messages_deleted: int (cuántos mensajes se borraron)
      - session_deleted: int (1 si se eliminó la fila de sesión, 0 en caso contrario)
    """
    with _connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS cnt FROM messages WHERE session_id = ?", (session_id,))
        msg_count = int(cur.fetchone()["cnt"])

        cur.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        session_deleted = cur.rowcount
        cur.execute("DELETE FROM apolo_state WHERE session_id = ?", (session_id,))
        apolo_deleted = cur.rowcount
        conn.commit()

    return {"had_conversation": msg_count > 0, "messages_deleted": msg_count, "session_deleted": session_deleted}