"""
Database Layer v4.4 — SQLite/PostgreSQL with v4.4 Schema
Supports inventory, orders, users, audit, settings, and more.
"""
import sqlite3, json, os, hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

DB_PATH = os.environ.get("WMS_DB_PATH", "wms_v44.db")

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        schema = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'operator',
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT,
            location TEXT,
            quantity INTEGER DEFAULT 0,
            reserved INTEGER DEFAULT 0,
            reorder_point INTEGER DEFAULT 10,
            max_stock INTEGER DEFAULT 1000,
            unit_cost REAL DEFAULT 0.0,
            category TEXT,
            zone TEXT,
            aisle TEXT,
            bin TEXT,
            last_counted TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer_id TEXT,
            status TEXT DEFAULT 'PENDING',
            priority TEXT DEFAULT 'NORMAL',
            total_items INTEGER DEFAULT 0,
            total_value REAL DEFAULT 0.0,
            shipping_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            promised_date TIMESTAMP,
            shipped_at TIMESTAMP,
            carrier TEXT,
            tracking_number TEXT
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            picked_qty INTEGER DEFAULT 0,
            packed_qty INTEGER DEFAULT 0,
            unit_price REAL DEFAULT 0.0,
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            details TEXT,
            prev_hash TEXT,
            curr_hash TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT UNIQUE NOT NULL,
            name TEXT,
            status TEXT DEFAULT 'ACTIVE',
            current_state TEXT DEFAULT 'INIT',
            context TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            workflow_id TEXT,
            type TEXT,
            status TEXT DEFAULT 'PENDING',
            assigned_to TEXT,
            priority INTEGER DEFAULT 5,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload TEXT,
            source TEXT,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);
        CREATE INDEX IF NOT EXISTS idx_inventory_location ON inventory(location);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        """
        conn = self._connect()
        conn.executescript(schema)
        conn.commit()
        conn.close()

    # ── Generic CRUD ─────────────────────────────────────────
    def execute(self, sql: str, params: tuple = ()) -> int:
        conn = self._connect()
        cur = conn.execute(sql, params)
        conn.commit()
        rowid = cur.lastrowid
        conn.close()
        return rowid

    def query(self, sql: str, params: tuple = ()) -> List[Dict]:
        conn = self._connect()
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        conn = self._connect()
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return dict(row) if row else None

    # ── Inventory ────────────────────────────────────────────
    def get_inventory(self, sku: Optional[str] = None) -> List[Dict]:
        if sku:
            return self.query("SELECT * FROM inventory WHERE sku = ?", (sku,))
        return self.query("SELECT * FROM inventory ORDER BY sku")

    def update_stock(self, sku: str, delta: int, reason: str = "") -> bool:
        self.execute("UPDATE inventory SET quantity = quantity + ?, updated_at = ? WHERE sku = ?",
                     (delta, datetime.now().isoformat(), sku))
        return True

    # ── Orders ───────────────────────────────────────────────
    def create_order(self, order_id: str, customer_id: str, items: List[Dict], **kwargs) -> int:
        oid = self.execute(
            "INSERT INTO orders (order_id, customer_id, status, priority, shipping_address) VALUES (?, ?, ?, ?, ?)",
            (order_id, customer_id, kwargs.get("status", "PENDING"), kwargs.get("priority", "NORMAL"), kwargs.get("shipping_address", ""))
        )
        for item in items:
            self.execute(
                "INSERT INTO order_items (order_id, sku, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, item["sku"], item["quantity"], item.get("unit_price", 0.0))
            )
        return oid

    def get_orders(self, status: Optional[str] = None) -> List[Dict]:
        if status:
            return self.query("SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC", (status,))
        return self.query("SELECT * FROM orders ORDER BY created_at DESC")

    # ── Users ────────────────────────────────────────────────
    def get_user(self, username: str) -> Optional[Dict]:
        return self.query_one("SELECT * FROM users WHERE username = ? AND active = 1", (username,))

    def create_user(self, username: str, password_hash: str, role: str = "operator", email: str = "") -> int:
        return self.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, role, email) VALUES (?, ?, ?, ?)",
            (username, password_hash, role, email)
        )

    # ── Settings ─────────────────────────────────────────────
    def get_setting(self, key: str, default: Any = None) -> Any:
        row = self.query_one("SELECT value FROM settings WHERE key = ?", (key,))
        return json.loads(row["value"]) if row else default

    def set_setting(self, key: str, value: Any):
        self.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, json.dumps(value), datetime.now().isoformat())
        )

    # ── Health ───────────────────────────────────────────────
    def get_stats(self) -> Dict:
        return {
            "inventory_count": self.query("SELECT COUNT(*) as c FROM inventory")[0]["c"],
            "order_count": self.query("SELECT COUNT(*) as c FROM orders")[0]["c"],
            "user_count": self.query("SELECT COUNT(*) as c FROM users")[0]["c"],
            "audit_count": self.query("SELECT COUNT(*) as c FROM audit_log")[0]["c"],
            "pending_tasks": self.query("SELECT COUNT(*) as c FROM tasks WHERE status = 'PENDING'")[0]["c"]
        }
