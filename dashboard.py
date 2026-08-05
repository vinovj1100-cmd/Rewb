"""
Dashboard Renderer v4.4 — Renders Guardian and system health data
"""
from typing import Dict, List
from guardian import Guardian, HealthStatus

class DashboardRenderer:
    def __init__(self, guardian: Guardian):
        self.guardian = guardian

    def render_health_table(self) -> List[Dict]:
        summary = self.guardian.get_health_summary()
        services = summary.get("services", {})
        return [
            {
                "service": name,
                "status": data["status"],
                "latency": f"{data['latency_ms']:.0f}ms",
                "uptime": f"{data['uptime_pct']:.2f}%",
                "message": data["message"]
            }
            for name, data in services.items()
        ]

    def render_resource_gauges(self) -> List[Dict]:
        summary = self.guardian.get_health_summary()
        resources = summary.get("resources", {})
        return [
            {
                "name": name,
                "value": data["value"],
                "unit": data["unit"],
                "threshold": data["threshold"],
                "pct": min(100, data["value"] / data["threshold"] * 100),
                "status": data["status"]
            }
            for name, data in resources.items()
        ]

    def render_alert_badge(self) -> Dict:
        summary = self.guardian.get_health_summary()
        overall = summary["overall"]
        colors = {"HEALTHY": "green", "DEGRADED": "orange", "CRITICAL": "red", "UNKNOWN": "gray"}
        return {
            "text": overall,
            "color": colors.get(overall, "gray"),
            "alert_count": summary["active_alerts"]
        }

    def render_full_dashboard(self) -> Dict:
        return {
            "health_badge": self.render_alert_badge(),
            "services": self.render_health_table(),
            "resources": self.render_resource_gauges(),
            "recent_alerts": self.guardian.get_alerts(10)
        }
