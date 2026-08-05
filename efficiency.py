"""
Efficiency Engine v4.4 — Wave planning, slotting, replenishment, KPIs
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class SlottingRecommendation:
    sku: str
    current_location: str
    recommended_location: str
    reason: str
    distance_savings: float

@dataclass
class ReplenishmentTask:
    sku: str
    from_location: str
    to_location: str
    quantity: int
    priority: str
    due_by: datetime

class EfficiencyEngine:
    def __init__(self):
        self.kpi_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.slotting_cache: Dict[str, Dict] = {}

    # ── Wave Planning ────────────────────────────────────────
    def plan_wave(self, orders: List[Dict], max_wave_size: int = 50) -> List[Dict]:
        """Group orders into waves based on zone affinity and priority."""
        waves = []
        current_wave = []
        current_zones = set()

        sorted_orders = sorted(orders, key=lambda o: o.get("priority", "NORMAL"))

        for order in sorted_orders:
            order_zones = set(order.get("zones", []))
            if len(current_wave) >= max_wave_size or (current_zones and not current_zones.intersection(order_zones)):
                waves.append({
                    "wave_id": f"WAVE-{len(waves)+1:03d}",
                    "orders": current_wave,
                    "zones": list(current_zones),
                    "order_count": len(current_wave)
                })
                current_wave = []
                current_zones = set()
            current_wave.append(order)
            current_zones.update(order_zones)

        if current_wave:
            waves.append({
                "wave_id": f"WAVE-{len(waves)+1:03d}",
                "orders": current_wave,
                "zones": list(current_zones),
                "order_count": len(current_wave)
            })
        return waves

    # ── Slotting Optimization ────────────────────────────────
    def optimize_slotting(self, inventory: List[Dict], pick_history: List[Dict]) -> List[SlottingRecommendation]:
        """Recommend slotting changes based on velocity and affinity."""
        # Calculate velocity scores
        velocity = {}
        for pick in pick_history:
            sku = pick["sku"]
            velocity[sku] = velocity.get(sku, 0) + pick["quantity"]

        recommendations = []
        for item in inventory:
            sku = item["sku"]
            vel = velocity.get(sku, 0)
            current_zone = item.get("zone", "")

            # Fast movers → front zones (A, B)
            if vel > 100 and current_zone.startswith("C"):
                recommendations.append(SlottingRecommendation(
                    sku=sku,
                    current_location=item["location"],
                    recommended_location=f"A-{np.random.randint(1, 20):02d}",
                    reason="High velocity item — move to fast-pick zone",
                    distance_savings=vel * 0.5
                ))
            # Slow movers → back zones
            elif vel < 10 and current_zone.startswith("A"):
                recommendations.append(SlottingRecommendation(
                    sku=sku,
                    current_location=item["location"],
                    recommended_location=f"D-{np.random.randint(1, 50):02d}",
                    reason="Low velocity item — move to bulk storage",
                    distance_savings=0
                ))
        return recommendations

    # ── Replenishment ────────────────────────────────────────
    def calculate_replenishment(self, inventory: List[Dict], 
                                pick_face_capacity: int = 50,
                                trigger_pct: float = 0.2) -> List[ReplenishmentTask]:
        """Generate replenishment tasks for pick faces below threshold."""
        tasks = []
        for item in inventory:
            qty = item.get("quantity", 0)
            capacity = item.get("pick_face_capacity", pick_face_capacity)
            if qty < capacity * trigger_pct:
                needed = capacity - qty
                tasks.append(ReplenishmentTask(
                    sku=item["sku"],
                    from_location=item.get("bulk_location", "BULK-01"),
                    to_location=item["location"],
                    quantity=needed,
                    priority="HIGH" if qty == 0 else "MEDIUM",
                    due_by=datetime.now() + timedelta(hours=4 if qty == 0 else 24)
                ))
        return tasks

    # ── KPIs ─────────────────────────────────────────────────
    def calculate_kpis(self, operations_data: Dict) -> Dict:
        picks = operations_data.get("picks", [])
        orders = operations_data.get("orders", [])

        total_picks = len(picks)
        accurate_picks = sum(1 for p in picks if p.get("accuracy", True))
        pick_accuracy = (accurate_picks / total_picks * 100) if total_picks > 0 else 100

        pick_times = [p.get("duration_seconds", 0) for p in picks]
        avg_pick_time = np.mean(pick_times) if pick_times else 0

        on_time_orders = sum(1 for o in orders if o.get("on_time", True))
        ship_on_time = (on_time_orders / len(orders) * 100) if orders else 100

        return {
            "pick_accuracy": round(pick_accuracy, 2),
            "avg_pick_time_sec": round(avg_pick_time, 1),
            "ship_on_time_pct": round(ship_on_time, 2),
            "orders_per_hour": round(len(orders) / 8, 1),
            "lines_per_hour": round(total_picks / 8, 1),
            "cost_per_order": round(operations_data.get("labor_cost", 0) / max(len(orders), 1), 2)
        }

    def record_kpi(self, name: str, value: float):
        if name not in self.kpi_history:
            self.kpi_history[name] = []
        self.kpi_history[name].append((datetime.now(), value))

    def get_kpi_trend(self, name: str, days: int = 7) -> List[Dict]:
        history = self.kpi_history.get(name, [])
        cutoff = datetime.now() - timedelta(days=days)
        return [
            {"date": h[0].isoformat(), "value": h[1]}
            for h in history if h[0] > cutoff
        ]
