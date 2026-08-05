"""
RBAC Engine v4.4 — Role-Based Access Control + Session Management
Supports roles, permissions, session tokens, and audit logging.
"""
import hashlib, secrets, time, json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class Permission:
    resource: str
    action: str  # read, write, delete, execute

@dataclass
class Role:
    name: str
    permissions: List[Permission] = field(default_factory=list)

@dataclass
class Session:
    token: str
    username: str
    role: str
    created_at: datetime
    expires_at: datetime
    data: Dict = field(default_factory=dict)

class RBACSession:
    def __init__(self, session_ttl_hours: int = 8):
        self.roles: Dict[str, Role] = {}
        self.sessions: Dict[str, Session] = {}
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self._init_default_roles()

    def _init_default_roles(self):
        self.roles["admin"] = Role("admin", [
            Permission("*", "*")
        ])
        self.roles["manager"] = Role("manager", [
            Permission("inventory", "read"), Permission("inventory", "write"),
            Permission("orders", "read"), Permission("orders", "write"),
            Permission("reports", "read"), Permission("users", "read"),
            Permission("settings", "read")
        ])
        self.roles["operator"] = Role("operator", [
            Permission("inventory", "read"), Permission("inventory", "write"),
            Permission("orders", "read"), Permission("orders", "write"),
            Permission("picking", "execute"), Permission("packing", "execute")
        ])
        self.roles["viewer"] = Role("viewer", [
            Permission("inventory", "read"),
            Permission("orders", "read"),
            Permission("reports", "read")
        ])

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str, hash: str) -> bool:
        return self.hash_password(password) == hash

    def create_session(self, username: str, role: str) -> str:
        token = secrets.token_urlsafe(32)
        now = datetime.now()
        session = Session(
            token=token,
            username=username,
            role=role,
            created_at=now,
            expires_at=now + self.session_ttl
        )
        self.sessions[token] = session
        return token

    def validate_session(self, token: str) -> Optional[Session]:
        session = self.sessions.get(token)
        if not session:
            return None
        if datetime.now() > session.expires_at:
            del self.sessions[token]
            return None
        return session

    def has_permission(self, token: str, resource: str, action: str) -> bool:
        session = self.validate_session(token)
        if not session:
            return False
        role = self.roles.get(session.role)
        if not role:
            return False
        for perm in role.permissions:
            if perm.resource == "*" or perm.resource == resource:
                if perm.action == "*" or perm.action == action:
                    return True
        return False

    def revoke_session(self, token: str):
        self.sessions.pop(token, None)

    def revoke_all_user_sessions(self, username: str):
        to_remove = [t for t, s in self.sessions.items() if s.username == username]
        for t in to_remove:
            del self.sessions[t]

    def get_active_sessions(self) -> List[Dict]:
        now = datetime.now()
        return [
            {"token": s.token[:8] + "...", "username": s.username, "role": s.role,
             "expires": s.expires_at.isoformat(), "remaining_minutes": int((s.expires_at - now).total_seconds() / 60)}
            for s in self.sessions.values() if s.expires_at > now
        ]

    def get_roles(self) -> List[str]:
        return list(self.roles.keys())

    def add_role(self, name: str, permissions: List[Dict]):
        perms = [Permission(p["resource"], p["action"]) for p in permissions]
        self.roles[name] = Role(name, perms)
