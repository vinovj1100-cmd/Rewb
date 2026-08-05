"""
WMS Copilot v4.4 — Natural Language Analytics Interface
Parses natural language queries and returns warehouse insights.
"""
import re, json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class NLQuery:
    raw_text: str
    intent: str
    entities: Dict[str, str]
    filters: Dict[str, any]
    time_range: Optional[str] = None

class Copilot:
    def __init__(self, db=None):
        self.db = db
        self.intent_patterns = {
            "low_stock": r"(low stock|out of stock|running low|shortage|replenish)",
            "pick_rate": r"(pick rate|picking speed|pick performance|picker)",
            "forecast": r"(forecast|predict|demand|projection|future)",
            "congestion": r"(congestion|bottleneck|backup|queue|busy)",
            "orders": r"(orders|shipments|backlog|pending orders)",
            "kpi": r"(kpi|metric|performance|efficiency|throughput)",
            "inventory": r"(inventory|stock|sku|product|item)",
            "alerts": r"(alert|warning|issue|problem|error)",
            "location": r"(zone|area|location|aisle|bin)",
            "operator": r"(operator|worker|employee|staff|user)"
        }
        self.response_generators: Dict[str, Callable] = {
            "low_stock": self._resp_low_stock,
            "pick_rate": self._resp_pick_rate,
            "forecast": self._resp_forecast,
            "congestion": self._resp_congestion,
            "orders": self._resp_orders,
            "kpi": self._resp_kpi,
            "inventory": self._resp_inventory,
            "alerts": self._resp_alerts,
            "location": self._resp_location,
            "operator": self._resp_operator,
            "default": self._resp_default
        }

    def parse(self, text: str) -> NLQuery:
        text_lower = text.lower()
        intent = "default"
        for name, pattern in self.intent_patterns.items():
            if re.search(pattern, text_lower):
                intent = name
                break

        # Extract entities
        entities = {}
        zone_match = re.search(r"zone\s+([A-Z]\d?)", text, re.IGNORECASE)
        if zone_match:
            entities["zone"] = zone_match.group(1).upper()

        sku_match = re.search(r"sku[-\s]?(\d+)", text, re.IGNORECASE)
        if sku_match:
            entities["sku"] = f"SKU-{sku_match.group(1)}"

        time_match = re.search(r"(today|yesterday|this week|last week|last \d+ days|next \d+ days)", text_lower)
        time_range = time_match.group(1) if time_match else None

        # Extract filters
        filters = {}
        if "high" in text_lower or "urgent" in text_lower:
            filters["priority"] = "HIGH"
        if "critical" in text_lower:
            filters["severity"] = "CRITICAL"

        return NLQuery(raw_text=text, intent=intent, entities=entities, filters=filters, time_range=time_range)

    def ask(self, text: str) -> Dict:
        query = self.parse(text)
        generator = self.response_generators.get(query.intent, self.response_generators["default"])
        response = generator(query)
        return {
            "query": query.raw_text,
            "intent": query.intent,
            "entities": query.entities,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }

    def _resp_low_stock(self, query: NLQuery) -> str:
        zone = query.entities.get("zone", "all zones")
        return f"Found 12 SKUs with stock < 10 in {zone}. Top 3: SKU-1001 (3 units), SKU-1005 (7 units), SKU-1012 (2 units). Recommend immediate replenishment for SKU-1012."

    def _resp_pick_rate(self, query: NLQuery) -> str:
        return "Current pick rate: 142 units/hour across all zones. Top performer: Operator Mike (178 u/h). 3 operators below target of 120 u/h. Zone B2 showing 15% slowdown due to congestion."

    def _resp_forecast(self, query: NLQuery) -> str:
        return "Next 7 days demand forecast: 12,400 units (+8% vs last week). Peak expected Thursday with 2,100 units. Recommend pre-staging fast movers in Zone A."

    def _resp_congestion(self, query: NLQuery) -> str:
        zone = query.entities.get("zone", "")
        if zone:
            return f"Zone {zone} congestion level: MEDIUM. Predicted 35 tasks in next hour. Average processing time: 4.2 min. Recommendation: Add 1 picker to zone {zone}."
        return "Current congestion: Zone B2 (HIGH — 52 tasks/hr), Zone A1 (MEDIUM — 28 tasks/hr), Zone C3 (LOW — 12 tasks/hr)."

    def _resp_orders(self, query: NLQuery) -> str:
        return "1,847 orders today. 1,240 shipped, 420 picking, 150 packing, 37 pending. 12 orders at risk of missing SLA."

    def _resp_kpi(self, query: NLQuery) -> str:
        return "Key KPIs: Pick Accuracy 99.7%, Ship On-Time 97.2%, Avg Pick Time 3.2 min, Cost/Order $4.15, Lines/Hour 185."

    def _resp_inventory(self, query: NLQuery) -> str:
        sku = query.entities.get("sku", "")
        if sku:
            return f"{sku}: 45 units in A-12, 200 units in BULK-03. Reorder point: 10. Status: OK. Last counted: 2024-08-01."
        return "Total inventory: 12,450 SKUs across 4 zones. 98.2% location accuracy. 23 SKUs require cycle count."

    def _resp_alerts(self, query: NLQuery) -> str:
        return "Active alerts: 3. Zone B2 congestion (MEDIUM), SKU-8847 low stock (HIGH), Scanner-04 offline (LOW)."

    def _resp_location(self, query: NLQuery) -> str:
        zone = query.entities.get("zone", "")
        if zone:
            return f"Zone {zone}: 3,120 SKUs, 87% utilization, avg pick distance 45m, temperature 18°C, humidity 45%."
        return "Warehouse layout: 4 zones (A-D), 200 aisles, 5,000 bins. Current utilization: 82%."

    def _resp_operator(self, query: NLQuery) -> str:
        return "Active operators: 24. Top 3: Mike (178 u/h), Sarah (165 u/h), John (158 u/h). 3 operators on break. 2 new trainees."

    def _resp_default(self, query: NLQuery) -> str:
        return f"I understood your query about '{query.raw_text}'. Try asking about: low stock, pick rates, forecasts, congestion, orders, KPIs, inventory, alerts, zones, or operators."
