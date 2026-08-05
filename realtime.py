"""
Realtime Event Bus v4.4 — Pub/Sub event system for warehouse operations
"""
import json, threading
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from queue import Queue

@dataclass
class Event:
    event_type: str
    payload: Dict
    source: str
    timestamp: str
    priority: int = 5

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_queue: Queue = Queue()
        self.event_history: List[Event] = []
        self.max_history = 10000
        self._lock = threading.Lock()
        self._running = False
        self._worker = None

    def subscribe(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        with self._lock:
            if event_type in self.subscribers:
                self.subscribers[event_type] = [c for c in self.subscribers[event_type] if c != callback]

    def publish(self, event_type: str, payload: Dict, source: str = "system", priority: int = 5):
        event = Event(
            event_type=event_type,
            payload=payload,
            source=source,
            timestamp=datetime.now().isoformat(),
            priority=priority
        )
        self.event_queue.put(event)
        with self._lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]

    def process_events(self):
        while not self.event_queue.empty():
            event = self.event_queue.get()
            with self._lock:
                callbacks = self.subscribers.get(event.event_type, []).copy()
                # Also call wildcard subscribers
                callbacks.extend(self.subscribers.get("*", []))
            for callback in callbacks:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Event handler error: {e}")
            self.event_queue.task_done()

    def start_worker(self):
        self._running = True
        def worker():
            while self._running:
                self.process_events()
                import time
                time.sleep(0.1)
        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def stop_worker(self):
        self._running = False
        if self._worker:
            self._worker.join(timeout=2)

    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        with self._lock:
            events = self.event_history
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            return [
                {"type": e.event_type, "payload": e.payload, "source": e.source,
                 "timestamp": e.timestamp, "priority": e.priority}
                for e in events[-limit:]
            ]

    def get_event_types(self) -> List[str]:
        with self._lock:
            return list(self.subscribers.keys())
