"""
Memory Store v4.4 — User settings, aliases, and preferences
"""
import json, os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

SETTINGS_FILE = "wms_settings.json"

@dataclass
class UserSettings:
    theme: str = "light"
    timezone: str = "UTC"
    page_size: int = 50
    default_zone: str = "A"
    notifications_enabled: bool = True
    email_alerts: bool = True
    slack_webhook: str = ""
    dashboard_layout: str = "default"
    language: str = "en"

@dataclass
class Alias:
    name: str
    expansion: str
    category: str = "general"

class MemoryStore:
    def __init__(self, filepath: str = SETTINGS_FILE):
        self.filepath = filepath
        self.settings: Dict[str, UserSettings] = {}
        self.aliases: Dict[str, Alias] = {}
        self.global_settings: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                self.settings = {k: UserSettings(**v) for k, v in data.get("settings", {}).items()}
                self.aliases = {k: Alias(**v) for k, v in data.get("aliases", {}).items()}
                self.global_settings = data.get("global", {})
            except Exception as e:
                print(f"MemoryStore load error: {e}")

    def _save(self):
        data = {
            "settings": {k: asdict(v) for k, v in self.settings.items()},
            "aliases": {k: asdict(v) for k, v in self.aliases.items()},
            "global": self.global_settings
        }
        with open(self.filepath, "w") as f:
            json.dump(data, f, indent=2)

    def get_user_settings(self, username: str) -> UserSettings:
        return self.settings.get(username, UserSettings())

    def set_user_settings(self, username: str, settings: UserSettings):
        self.settings[username] = settings
        self._save()

    def update_user_setting(self, username: str, key: str, value: Any):
        settings = self.get_user_settings(username)
        if hasattr(settings, key):
            setattr(settings, key, value)
            self.set_user_settings(username, settings)

    def add_alias(self, name: str, expansion: str, category: str = "general"):
        self.aliases[name] = Alias(name, expansion, category)
        self._save()

    def resolve_alias(self, text: str) -> str:
        for alias in self.aliases.values():
            text = text.replace(alias.name, alias.expansion)
        return text

    def get_global(self, key: str, default: Any = None) -> Any:
        return self.global_settings.get(key, default)

    def set_global(self, key: str, value: Any):
        self.global_settings[key] = value
        self._save()
