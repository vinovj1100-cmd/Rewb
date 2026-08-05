"""
Workflow Engine v4.4 — State Machine for Order/Inventory Workflows
Supports transitions, guards, actions, and parallel states.
"""
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

class State(Enum):
    INIT = "INIT"
    PENDING = "PENDING"
    PICKING = "PICKING"
    PICKED = "PICKED"
    PACKING = "PACKING"
    PACKED = "PACKED"
    SHIPPING = "SHIPPING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"
    RETURNED = "RETURNED"

@dataclass
class Transition:
    from_state: State
    to_state: State
    trigger: str
    guard: Optional[Callable] = None
    action: Optional[Callable] = None
    name: str = ""

@dataclass
class WorkflowInstance:
    workflow_id: str
    name: str
    current_state: State = State.INIT
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    active: bool = True

class WorkflowEngine:
    def __init__(self):
        self.transitions: List[Transition] = []
        self.instances: Dict[str, WorkflowInstance] = {}
        self._build_default_workflows()

    def _build_default_workflows(self):
        # Standard order fulfillment workflow
        self.add_transition(State.INIT, State.PENDING, "create")
        self.add_transition(State.PENDING, State.PICKING, "start_pick")
        self.add_transition(State.PICKING, State.PICKED, "complete_pick")
        self.add_transition(State.PICKED, State.PACKING, "start_pack")
        self.add_transition(State.PACKING, State.PACKED, "complete_pack")
        self.add_transition(State.PACKED, State.SHIPPING, "ship")
        self.add_transition(State.SHIPPING, State.SHIPPED, "confirm_ship")
        self.add_transition(State.SHIPPED, State.DELIVERED, "deliver")
        self.add_transition(State.PENDING, State.ON_HOLD, "hold")
        self.add_transition(State.ON_HOLD, State.PENDING, "release")
        self.add_transition(State.PENDING, State.CANCELLED, "cancel")
        self.add_transition(State.PICKING, State.CANCELLED, "cancel")
        self.add_transition(State.SHIPPED, State.RETURNED, "return")

    def add_transition(self, from_state: State, to_state: State, trigger: str,
                       guard: Optional[Callable] = None, action: Optional[Callable] = None):
        self.transitions.append(Transition(from_state, to_state, trigger, guard, action,
                                           name=f"{from_state.value}_{to_state.value}"))

    def create_instance(self, workflow_id: str, name: str = "", context: Optional[Dict] = None) -> WorkflowInstance:
        inst = WorkflowInstance(workflow_id=workflow_id, name=name or workflow_id,
                                context=context or {})
        self.instances[workflow_id] = inst
        return inst

    def trigger(self, workflow_id: str, event: str, context_update: Optional[Dict] = None) -> bool:
        inst = self.instances.get(workflow_id)
        if not inst or not inst.active:
            return False

        candidates = [t for t in self.transitions
                      if t.from_state == inst.current_state and t.trigger == event]
        if not candidates:
            return False

        for t in candidates:
            if t.guard and not t.guard(inst.context):
                continue
            # Execute transition
            old_state = inst.current_state
            inst.current_state = t.to_state
            if context_update:
                inst.context.update(context_update)
            inst.history.append({
                "from": old_state.value,
                "to": t.to_state.value,
                "trigger": event,
                "timestamp": self._now()
            })
            if t.action:
                t.action(inst)
            return True
        return False

    def get_available_transitions(self, workflow_id: str) -> List[str]:
        inst = self.instances.get(workflow_id)
        if not inst:
            return []
        return [t.trigger for t in self.transitions if t.from_state == inst.current_state]

    def get_instance(self, workflow_id: str) -> Optional[WorkflowInstance]:
        return self.instances.get(workflow_id)

    def _now(self):
        from datetime import datetime
        return datetime.now().isoformat()

    def to_dict(self, workflow_id: str) -> Dict:
        inst = self.instances.get(workflow_id)
        if not inst:
            return {}
        return {
            "workflow_id": inst.workflow_id,
            "name": inst.name,
            "current_state": inst.current_state.value,
            "context": inst.context,
            "history": inst.history,
            "active": inst.active
        }
