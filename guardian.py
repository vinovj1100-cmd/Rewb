"""
Guardian v4.4 — System Health Monitoring
Monitors services, resources, and performance metrics.
"""
import time, json, os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

@dataclass
class ServiceCheck:
    name: str
    status: HealthStatus
    latency_ms: float
    uptime_pct: float
    last_check: datetime
    message: str = ""

@dataclass
class ResourceMetric:
    name: str
    value: float
    unit: str
    threshold: float
    status: HealthStatus

class Guardian:
    def __init__(self):
        self.services: Dict[str, ServiceCheck] = {}
        self.resources: Dict[str, ResourceMetric] = {}
        self.alerts: List[Dict] = []
        self.check_interval_sec = 30
        self._init_defaults()

    def _init_defaults(self):
        self.services = {
            "database": ServiceCheck("Database", HealthStatus.HEALTHY, 12.0, 99.99, datetime.now()),
            "redis": ServiceCheck("Redis", HealthStatus.HEALTHY, 5.0, 99.95, datetime.now()),
            "api_gateway": ServiceCheck("API Gateway", HealthStatus.HEALTHY, 25.0, 99.9, datetime.now()),
            "message_queue": ServiceCheck("Message Queue", HealthStatus.HEALTHY, 8.0, 99.98, datetime.now()),
            "ai_engine": ServiceCheck("AI Engine", HealthStatus.HEALTHY, 45.0, 99.9, datetime.now()),
            "label_processor": ServiceCheck("Label Processor", HealthStatus.HEALTHY, 15.0, 99.9, datetime.now()),
        }
        self.resources = {
            "cpu": ResourceMetric("CPU", 34.0, "%", 80.0, HealthStatus.HEALTHY),
            "memory": ResourceMetric("Memory", 62.0, "%", 85.0, HealthStatus.HEALTHY),
            "disk": ResourceMetric("Disk", 45.0, "%", 90.0, HealthStatus.HEALTHY),
            "db_connections": ResourceMetric("DB Connections", 12.0, "count", 80.0, HealthStatus.HEALTHY),
        }

    def check_service(self, name: str, latency_ms: float, error: bool = False) -> ServiceCheck:
        svc = self.services.get(name)
        if not svc:
            svc = ServiceCheck(name, HealthStatus.UNKNOWN, latency_ms, 100.0, datetime.now())
            self.services[name] = svc

        svc.last_check = datetime.now()
        svc.latency_ms = latency_ms

        if error:
            svc.status = HealthStatus.CRITICAL
            svc.message = "Service reported error"
        elif latency_ms > 100:
            svc.status = HealthStatus.DEGRADED
            svc.message = f"High latency: {latency_ms}ms"
        else:
            svc.status = HealthStatus.HEALTHY
            svc.message = "OK"

        if svc.status != HealthStatus.HEALTHY:
            self.alerts.append({
                "time": datetime.now().isoformat(),
                "service": name,
                "status": svc.status.value,
                "message": svc.message
            })
        return svc

    def check_resource(self, name: str, value: float):
        res = self.resources.get(name)
        if not res:
            return
        res.value = value
        if value >= res.threshold:
            res.status = HealthStatus.CRITICAL
        elif value >= res.threshold * 0.8:
            res.status = HealthStatus.DEGRADED
        else:
            res.status = HealthStatus.HEALTHY

    def get_health_summary(self) -> Dict:
        svc_statuses = [s.status for s in self.services.values()]
        overall = HealthStatus.HEALTHY
        if any(s == HealthStatus.CRITICAL for s in svc_statuses):
            overall = HealthStatus.CRITICAL
        elif any(s == HealthStatus.DEGRADED for s in svc_statuses):
            overall = HealthStatus.DEGRADED

        return {
            "overall": overall.value,
            "services": {name: {"status": s.status.value, "latency_ms": s.latency_ms,
                               "uptime_pct": s.uptime_pct, "message": s.message}
                        for name, s in self.services.items()},
            "resources": {name: {"value": r.value, "unit": r.unit, "threshold": r.threshold,
                                "status": r.status.value}
                         for name, r in self.resources.items()},
            "active_alerts": len([a for a in self.alerts if a["status"] != "HEALTHY"]),
            "last_check": datetime.now().isoformat()
        }

    def get_alerts(self, limit: int = 50) -> List[Dict]:
        return self.alerts[-limit:]

    def clear_alerts(self):
        self.alerts = []
