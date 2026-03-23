"""
Session Manager Service
Manages in-memory session lifecycle
"""
import uuid
from datetime import datetime
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage user sessions (in-memory, no database)"""
    
    def __init__(self, max_sessions: int = 100):
        self.sessions: Dict[str, dict] = {}
        self.max_sessions = max_sessions
    
    def create_session(self) -> str:
        """Create new session"""
        if len(self.sessions) >= self.max_sessions:
            # Remove oldest session
            oldest = min(self.sessions.items(), key=lambda x: x[1]["created_at"])
            del self.sessions[oldest[0]]
            logger.warning(f"Max sessions reached, removed old session")
        
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "image_count": 0
        }
        logger.info(f"Session created: {session_id[:8]}...")
        return session_id
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists"""
        return session_id in self.sessions
    
    def clear_session(self, session_id: str) -> bool:
        """Remove session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Session removed: {session_id[:8]}...")
            return True
        return False
    
    def get_active_count(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)
    
    def update_image_count(self, session_id: str, delta: int = 1):
        """Update image count in session"""
        if session_id in self.sessions:
            self.sessions[session_id]["image_count"] += delta
