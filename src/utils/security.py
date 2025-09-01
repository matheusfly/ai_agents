from typing import Dict, Any, List, Optional
import hashlib
import secrets
import time
import json
from datetime import datetime
import os


class SecurityManager:
    """Security manager for the multi-agent system."""
    
    def __init__(self, audit_log_path: str = "./audit_logs"):
        self.audit_log_path = audit_log_path
        os.makedirs(audit_log_path, exist_ok=True)
        self.active_sessions = {}
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return self.hash_password(password) == hashed
    
    def create_session(self, user_id: str, permissions: List[str]) -> str:
        """Create a new session for a user."""
        session_id = secrets.token_urlsafe(32)
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "permissions": permissions,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a session and return session info if valid."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            # Check if session is still valid (e.g., not expired)
            if time.time() - session["last_activity"] < 3600:  # 1 hour timeout
                session["last_activity"] = time.time()
                return session
        return None
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def has_permission(self, session_id: str, permission: str) -> bool:
        """Check if a session has a specific permission."""
        session = self.validate_session(session_id)
        if session:
            return permission in session["permissions"]
        return False
    
    def log_audit_event(self, event_type: str, user_id: str, details: Dict[str, Any]) -> None:
        """Log an audit event."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }
        
        # Write to audit log file
        log_file = os.path.join(self.audit_log_path, f"audit_{datetime.now().strftime('%Y-%m-%d')}.json")
        
        # Read existing entries
        entries = []
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    entries = json.load(f)
            except:
                entries = []
        
        # Add new entry
        entries.append(audit_entry)
        
        # Write back to file
        with open(log_file, 'w') as f:
            json.dump(entries, f, indent=2)
    
    def get_audit_logs(self, date: str = None) -> List[Dict[str, Any]]:
        """Get audit logs for a specific date or today."""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        log_file = os.path.join(self.audit_log_path, f"audit_{date}.json")
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        
        return []


class AccessControl:
    """Access control for different system components."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.permissions = {
            "read_prompts": "Read prompt history",
            "write_prompts": "Create and modify prompts",
            "execute_workflows": "Execute multi-agent workflows",
            "view_logs": "View system logs",
            "manage_users": "Manage user accounts",
            "admin": "Full administrative access"
        }
    
    def check_permission(self, session_id: str, permission: str) -> bool:
        """Check if a session has a specific permission."""
        return self.security_manager.has_permission(session_id, permission)
    
    def require_permission(self, session_id: str, permission: str) -> None:
        """Require a specific permission, raising an exception if not granted."""
        if not self.check_permission(session_id, permission):
            raise PermissionError(f"Permission '{permission}' required but not granted")
    
    def get_user_permissions(self, session_id: str) -> List[str]:
        """Get all permissions for a user session."""
        session = self.security_manager.validate_session(session_id)
        if session:
            return session["permissions"]
        return []


# Global instances
security_manager = SecurityManager()
access_control = AccessControl(security_manager)