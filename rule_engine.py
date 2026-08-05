"""
Rule Engine v4.4 — YAML-driven business rules
Supports conditions, actions, priorities, and rule chaining.
"""
import yaml, json, re
from typing import Dict, List, Any, Callable
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Rule:
    id: str
    name: str
    condition: str
    action: str
    priority: int = 5
    active: bool = True
    metadata: Dict[str, Any] = None

class RuleEngine:
    def __init__(self, config_path: str = "config.yaml"):
        self.rules: List[Rule] = []
        self.actions: Dict[str, Callable] = {}
        self.config_path = config_path
        self._register_default_actions()
        self.load_rules()

    def _register_default_actions(self):
        self.actions = {
            "alert": lambda ctx, msg: print(f"[ALERT] {msg}"),
            "set_priority": lambda ctx, val: ctx.update({"priority": val}),
            "hold_order": lambda ctx, reason: ctx.update({"status": "ON_HOLD", "hold_reason": reason}),
            "route_zone": lambda ctx, zone: ctx.update({"zone": zone}),
            "flag_review": lambda ctx, reason: ctx.update({"review": True, "review_reason": reason}),
            "auto_approve": lambda ctx, _: ctx.update({"approved": True}),
            "notify_manager": lambda ctx, msg: ctx.update({"notifications": ctx.get("notifications", []) + [msg]}),
        }

    def load_rules(self):
        path = Path(self.config_path)
        if not path.exists():
            self._create_default_config()
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            rules_data = data.get("rules", [])
            self.rules = []
            for r in rules_data:
                self.rules.append(Rule(
                    id=r.get("id", "R" + str(len(self.rules))),
                    name=r.get("name", "Unnamed"),
                    condition=r.get("condition", "True"),
                    action=r.get("action", ""),
                    priority=r.get("priority", 5),
                    active=r.get("active", True),
                    metadata=r.get("metadata", {})
                ))
            self.rules.sort(key=lambda r: r.priority)
        except Exception as e:
            print(f"RuleEngine load error: {e}")

    def _create_default_config(self):
        default = {
            "rules": [
                {"id": "R001", "name": "High Value Alert", "condition": "order_value > 1000", "action": "flag_review:High value order requires approval", "priority": 1},
                {"id": "R002", "name": "Low Stock Hold", "condition": "stock < reorder_point", "action": "hold_order:Insufficient stock", "priority": 1},
                {"id": "R003", "name": "Express Route", "condition": "service_type == 'EXPRESS'", "action": "set_priority:URGENT", "priority": 2},
                {"id": "R004", "name": "Damaged Flag", "condition": "quality_score < 0.5", "action": "flag_review:Quality check failed", "priority": 1},
                {"id": "R005", "name": "VIP Customer", "condition": "customer_tier == 'PLATINUM'", "action": "set_priority:HIGH", "priority": 2},
                {"id": "R006", "name": "Auto Approve Small", "condition": "order_value < 50 and customer_tier == 'GOLD'", "action": "auto_approve:true", "priority": 3},
            ]
        }
        with open(self.config_path, "w") as f:
            yaml.dump(default, f, default_flow_style=False)

    def evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        try:
            # Simple expression evaluator
            expr = condition
            for key, val in context.items():
                if isinstance(val, str):
                    expr = expr.replace(key, f"'{val}'")
                else:
                    expr = expr.replace(key, str(val))
            return eval(expr, {"__builtins__": {}}, {})
        except:
            return False

    def evaluate(self, context: Dict[str, Any]) -> List[Dict]:
        triggered = []
        for rule in self.rules:
            if not rule.active:
                continue
            if self.evaluate_condition(rule.condition, context):
                action_parts = rule.action.split(":", 1)
                action_name = action_parts[0]
                action_param = action_parts[1] if len(action_parts) > 1 else ""
                if action_name in self.actions:
                    self.actions[action_name](context, action_param)
                triggered.append({
                    "rule_id": rule.id,
                    "rule_name": rule.name,
                    "action": rule.action,
                    "priority": rule.priority
                })
        return triggered

    def add_rule(self, rule: Rule):
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority)

    def get_rules(self) -> List[Dict]:
        return [{"id": r.id, "name": r.name, "condition": r.condition,
                 "action": r.action, "priority": r.priority, "active": r.active} for r in self.rules]
