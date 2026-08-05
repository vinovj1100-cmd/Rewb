"""
Offline Sync v4.4 — Queue-based offline operation sync
Handles disconnected operations and syncs when connection restored.
"""
import json, time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from queue import Queue

@dataclass
class SyncOperation:
    op_id: str
    operation: str  # CREATE, UPDATE, DELETE
    entity_type: str
    entity_id: str
    data: Dict
    timestamp: str
    synced: bool = False
    retry_count: int = 0
    error: str = ""

class OfflineQueue:
    def __init__(self, max_retries: int = 3):
        self.queue: List[SyncOperation] = []
        self.max_retries = max_retries
        self.synced_count = 0
        self.failed_count = 0

    def enqueue(self, operation: str, entity_type: str, entity_id: str, data: Dict) -> str:
        op = SyncOperation(
            op_id=f"SYNC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(self.queue)}",
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            data=data,
            timestamp=datetime.now().isoformat()
        )
        self.queue.append(op)
        return op.op_id

    def sync_all(self, sync_handler: Optional[callable] = None) -> Dict:
        results = {"synced": 0, "failed": 0, "pending": 0}
        for op in self.queue:
            if op.synced:
                continue
            if op.retry_count >= self.max_retries:
                results["failed"] += 1
                continue

            try:
                if sync_handler:
                    sync_handler(op)
                op.synced = True
                self.synced_count += 1
                results["synced"] += 1
            except Exception as e:
                op.retry_count += 1
                op.error = str(e)
                results["failed"] += 1

        results["pending"] = len([o for o in self.queue if not o.synced and o.retry_count < self.max_retries])
        return results

    def get_pending(self) -> List[Dict]:
        return [
            {"op_id": o.op_id, "operation": o.operation, "entity": o.entity_type,
             "entity_id": o.entity_id, "retries": o.retry_count, "error": o.error}
            for o in self.queue if not o.synced
        ]

    def get_stats(self) -> Dict:
        total = len(self.queue)
        synced = sum(1 for o in self.queue if o.synced)
        failed = sum(1 for o in self.queue if o.retry_count >= self.max_retries)
        pending = total - synced - failed
        return {
            "total": total,
            "synced": synced,
            "failed": failed,
            "pending": pending,
            "sync_rate": round(synced / total * 100, 1) if total > 0 else 100
        }

    def clear_synced(self):
        self.queue = [o for o in self.queue if not o.synced]
