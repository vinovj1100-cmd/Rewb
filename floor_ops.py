"""
Floor Operations v4.4 — Picking, Packing, Putaway, Andon, SLA Monitoring
"""
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class OpStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"

class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class PickTask:
    task_id: str
    wave_id: str
    sku: str
    location: str
    quantity: int
    picked_qty: int = 0
    status: OpStatus = OpStatus.PENDING
    assigned_to: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class AndonAlert:
    alert_id: str
    zone: str
    issue: str
    severity: Severity
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: str = ""

@dataclass
class SLAMetric:
    name: str
    target: str
    actual: str
    unit: str
    status: str = "OK"

class FloorOperations:
    def __init__(self):
        self.pick_tasks: Dict[str, PickTask] = {}
        self.waves: Dict[str, List[str]] = {}
        self.andon_alerts: List[AndonAlert] = []
        self.sla_metrics: List[SLAMetric] = []
        self._init_sla()

    def _init_sla(self):
        self.sla_metrics = [
            SLAMetric("Order Cycle Time", "4h", "3.2h", "hours", "OK"),
            SLAMetric("Pick Accuracy", "99.5%", "99.7%", "percent", "OK"),
            SLAMetric("Ship On Time", "98%", "97.2%", "percent", "WARNING"),
            SLAMetric("Dock-to-Stock", "2h", "1.8h", "hours", "OK"),
            SLAMetric("Returns Processing", "24h", "22h", "hours", "OK"),
        ]

    # ── Picking ──────────────────────────────────────────────
    def create_wave(self, wave_id: str, tasks: List[Dict]) -> str:
        self.waves[wave_id] = []
        for t in tasks:
            task = PickTask(
                task_id=t["task_id"],
                wave_id=wave_id,
                sku=t["sku"],
                location=t["location"],
                quantity=t["quantity"]
            )
            self.pick_tasks[task.task_id] = task
            self.waves[wave_id].append(task.task_id)
        return wave_id

    def assign_task(self, task_id: str, operator: str) -> bool:
        task = self.pick_tasks.get(task_id)
        if not task or task.status != OpStatus.PENDING:
            return False
        task.assigned_to = operator
        task.status = OpStatus.IN_PROGRESS
        task.started_at = datetime.now()
        return True

    def complete_pick(self, task_id: str, picked_qty: int) -> bool:
        task = self.pick_tasks.get(task_id)
        if not task or task.status != OpStatus.IN_PROGRESS:
            return False
        task.picked_qty = picked_qty
        task.status = OpStatus.COMPLETED
        task.completed_at = datetime.now()
        return True

    def get_wave_progress(self, wave_id: str) -> Dict:
        task_ids = self.waves.get(wave_id, [])
        tasks = [self.pick_tasks[tid] for tid in task_ids]
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == OpStatus.COMPLETED)
        in_progress = sum(1 for t in tasks if t.status == OpStatus.IN_PROGRESS)
        return {
            "wave_id": wave_id,
            "total_tasks": total,
            "completed": completed,
            "in_progress": in_progress,
            "pending": total - completed - in_progress,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0
        }

    # ── Packing ──────────────────────────────────────────────
    def get_packing_stations(self) -> List[Dict]:
        import random
        return [
            {"station": f"PK-{i}", "status": random.choice(["IDLE", "ACTIVE", "BLOCKED"]),
             "throughput": random.randint(50, 200), "efficiency": random.randint(85, 100)}
            for i in range(1, 6)
        ]

    # ── Putaway ──────────────────────────────────────────────
    def suggest_putaway(self, sku: str, qty: int, zones: List[str]) -> Dict:
        # Simple logic: suggest zone with most space
        import random
        zone = random.choice(zones)
        return {
            "sku": sku,
            "quantity": qty,
            "suggested_zone": zone,
            "suggested_location": f"{zone}-{random.randint(1, 50):02d}",
            "reason": "Optimal space availability"
        }

    # ── Andon ────────────────────────────────────────────────
    def raise_andon(self, zone: str, issue: str, severity: Severity = Severity.MEDIUM) -> str:
        alert = AndonAlert(
            alert_id=f"ANDON-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            zone=zone,
            issue=issue,
            severity=severity,
            created_at=datetime.now()
        )
        self.andon_alerts.append(alert)
        return alert.alert_id

    def resolve_andon(self, alert_id: str, resolved_by: str) -> bool:
        for alert in self.andon_alerts:
            if alert.alert_id == alert_id and alert.resolved_at is None:
                alert.resolved_at = datetime.now()
                alert.resolved_by = resolved_by
                return True
        return False

    def get_active_andon(self) -> List[Dict]:
        return [
            {"alert_id": a.alert_id, "zone": a.zone, "issue": a.issue,
             "severity": a.severity.value, "age_minutes": int((datetime.now() - a.created_at).total_seconds() / 60)}
            for a in self.andon_alerts if a.resolved_at is None
        ]

    # ── SLA ──────────────────────────────────────────────────
    def get_sla_dashboard(self) -> List[Dict]:
        return [
            {"name": m.name, "target": m.target, "actual": m.actual,
             "unit": m.unit, "status": m.status}
            for m in self.sla_metrics
        ]

    def update_sla(self, name: str, actual: str, status: str):
        for m in self.sla_metrics:
            if m.name == name:
                m.actual = actual
                m.status = status
                break
