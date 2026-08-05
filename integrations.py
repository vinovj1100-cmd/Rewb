"""
Integration Facade v4.4 — Unified interface for external system integrations
Supports ERP, TMS, EDI, and API connectors.
"""
import json, requests
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class IntegrationConfig:
    name: str
    endpoint: str
    auth_type: str  # api_key, oauth2, basic
    credentials: Dict
    enabled: bool = True
    timeout: int = 30

class BaseConnector(ABC):
    def __init__(self, config: IntegrationConfig):
        self.config = config

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def send(self, data: Dict) -> Dict:
        pass

    @abstractmethod
    def receive(self) -> List[Dict]:
        pass

class ERPConnector(BaseConnector):
    def connect(self) -> bool:
        return self.config.enabled

    def send(self, data: Dict) -> Dict:
        return {"status": "sent", "system": "ERP", "data": data}

    def receive(self) -> List[Dict]:
        return [{"type": "inventory_update", "sku": "SKU-1001", "qty": 100}]

class TMSConnector(BaseConnector):
    def connect(self) -> bool:
        return self.config.enabled

    def send(self, data: Dict) -> Dict:
        return {"status": "sent", "system": "TMS", "shipment_id": data.get("shipment_id")}

    def receive(self) -> List[Dict]:
        return [{"type": "tracking_update", "tracking": "TRK123456", "status": "in_transit"}]

class EDIConnector(BaseConnector):
    def connect(self) -> bool:
        return self.config.enabled

    def send(self, data: Dict) -> Dict:
        return {"status": "sent", "system": "EDI", "message_type": data.get("message_type", "850")}

    def receive(self) -> List[Dict]:
        return [{"type": "purchase_order", "po_number": "PO-12345", "items": 5}]

class IntegrationFacade:
    def __init__(self):
        self.connectors: Dict[str, BaseConnector] = {}
        self.configs: Dict[str, IntegrationConfig] = {}

    def register_connector(self, name: str, connector: BaseConnector):
        self.connectors[name] = connector
        self.configs[name] = connector.config

    def get_connector(self, name: str) -> Optional[BaseConnector]:
        return self.connectors.get(name)

    def send_to_all(self, data: Dict) -> Dict[str, Dict]:
        results = {}
        for name, connector in self.connectors.items():
            if connector.config.enabled:
                try:
                    results[name] = connector.send(data)
                except Exception as e:
                    results[name] = {"status": "error", "error": str(e)}
        return results

    def get_status(self) -> Dict[str, Dict]:
        return {
            name: {"enabled": c.enabled, "endpoint": c.endpoint, "connected": conn.connect()}
            for name, (c, conn) in [(n, (self.configs[n], self.connectors[n])) for n in self.connectors]
        }

    def create_default_integrations(self):
        erp = ERPConnector(IntegrationConfig("ERP", "https://erp.example.com/api", "api_key", {"key": "***"}))
        tms = TMSConnector(IntegrationConfig("TMS", "https://tms.example.com/api", "oauth2", {"token": "***"}))
        edi = EDIConnector(IntegrationConfig("EDI", "sftp://edi.example.com", "basic", {"user": "wms", "pass": "***"}))
        self.register_connector("ERP", erp)
        self.register_connector("TMS", tms)
        self.register_connector("EDI", edi)
