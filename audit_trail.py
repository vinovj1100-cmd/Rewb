"""
Audit Trail v4.4 — Hash-chained immutable audit log
Each entry contains a hash of the previous entry, creating a tamper-evident chain.
"""
import hashlib, json, sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AuditEntry:
    timestamp: str
    user_id: str
    action: str
    entity_type: str
    entity_id: str
    details: str
    prev_hash: str
    curr_hash: str

class AuditTrail:
    def __init__(self, db_path: str = "wms_v44.db"):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                details TEXT,
                prev_hash TEXT,
                curr_hash TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _get_last_hash(self) -> str:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT curr_hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
        conn.close()
        return row[0] if row else "0" * 64

    def _compute_hash(self, entry: Dict) -> str:
        data = json.dumps(entry, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def log(self, user_id: str, action: str, entity_type: str = "", entity_id: str = "", details: str = "") -> str:
        prev_hash = self._get_last_hash()
        entry_data = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details,
            "prev_hash": prev_hash
        }
        curr_hash = self._compute_hash(entry_data)

        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO audit_log (timestamp, user_id, action, entity_type, entity_id, details, prev_hash, curr_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (entry_data["timestamp"], user_id, action, entity_type, entity_id, details, prev_hash, curr_hash)
        )
        conn.commit()
        conn.close()
        return curr_hash

    def get_entries(self, limit: int = 100, offset: int = 0, user_id: Optional[str] = None) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (user_id, limit, offset)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def verify_chain(self) -> Dict:
        """Verify the integrity of the entire audit chain."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id ASC").fetchall()
        conn.close()

        if not rows:
            return {"valid": True, "entries_checked": 0, "first_broken": None}

        prev_hash = "0" * 64
        for i, row in enumerate(rows):
            entry_data = {
                "timestamp": row["timestamp"],
                "user_id": row["user_id"],
                "action": row["action"],
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "details": row["details"],
                "prev_hash": prev_hash
            }
            computed = self._compute_hash(entry_data)
            if computed != row["curr_hash"]:
                return {"valid": False, "entries_checked": i + 1, "first_broken": row["id"]}
            prev_hash = row["curr_hash"]

        return {"valid": True, "entries_checked": len(rows), "first_broken": None}

    def export(self, format: str = "json") -> str:
        entries = self.get_entries(limit=10000)
        if format == "json":
            return json.dumps(entries, indent=2)
        elif format == "csv":
            if not entries:
                return ""
            headers = entries[0].keys()
            lines = [",".join(headers)]
            for e in entries:
                lines.append(",".join(str(e.get(h, "")) for h in headers))
            return "\n".join(lines)
        return ""
