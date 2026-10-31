"""
Authentication and Cryptographic Security Module.
Implements PBKDF2-HMAC-SHA256 password hashing, session tokens, and brute-force rate limiting.
"""

import hashlib
import secrets
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from database.connection import db_manager


class AuthSecurityManager:
    """
    Manages user authentication, password hashing, and login rate limiting.
    """

    def __init__(self, max_attempts: int = 5, lock_duration_sec: int = 300):
        self.max_attempts = max_attempts
        self.lock_duration_sec = lock_duration_sec
        self._failed_attempts: Dict[str, list] = {}  # username -> list of timestamps
        self._active_sessions: Dict[str, Dict[str, Any]] = {}  # token -> session dict

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hashes password with PBKDF2-HMAC-SHA256 and unique 16-byte salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000,
        ).hex()
        return pwd_hash, salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Verifies candidate password against stored hash using constant-time comparison."""
        candidate_hash, _ = AuthSecurityManager.hash_password(password, salt=salt)
        return secrets.compare_digest(candidate_hash, password_hash)

    def _is_rate_limited(self, username: str) -> bool:
        """Checks if account is temporarily locked due to repeated failed logins."""
        now = time.time()
        attempts = self._failed_attempts.get(username, [])
        # Filter attempts within the lock duration window
        recent = [t for t in attempts if now - t < self.lock_duration_sec]
        self._failed_attempts[username] = recent
        return len(recent) >= self.max_attempts

    def _record_failure(self, username: str) -> None:
        attempts = self._failed_attempts.setdefault(username, [])
        attempts.append(time.time())

    def _clear_failures(self, username: str) -> None:
        self._failed_attempts.pop(username, None)

    def create_user(self, username: str, password: str, role: str = "operator") -> bool:
        """Registers a new user into SQLite users table."""
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        pwd_hash, salt = self.hash_password(password)
        now_utc = datetime.now(timezone.utc).isoformat()
        query = """
        INSERT INTO users (username, password_hash, salt, role, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
        """
        try:
            with db_manager.session() as conn:
                conn.execute(query, (username.strip().lower(), pwd_hash, salt, role, now_utc))
                return True
        except Exception:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Validates credentials and returns session payload if authenticated.
        Returns None on invalid credentials or rate limiting.
        """
        user_key = username.strip().lower()
        if self._is_rate_limited(user_key):
            return {"error": "Account temporarily locked due to excessive failed attempts. Please wait 5 minutes."}

        query = "SELECT id, username, password_hash, salt, role, is_active FROM users WHERE username = ?"
        with db_manager.session() as conn:
            cursor = conn.execute(query, (user_key,))
            row = cursor.fetchone()

        if not row or not row["is_active"]:
            self._record_failure(user_key)
            return None

        if not self.verify_password(password, row["password_hash"], row["salt"]):
            self._record_failure(user_key)
            return None

        # Successful login
        self._clear_failures(user_key)
        now_utc = datetime.now(timezone.utc).isoformat()
        with db_manager.session() as conn:
            conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_utc, row["id"]))

        # Generate secure session token
        token = secrets.token_urlsafe(32)
        session_data = {
            "token": token,
            "user_id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "login_time": now_utc,
        }
        self._active_sessions[token] = session_data
        return session_data

    def validate_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Returns session data if token is active."""
        return self._active_sessions.get(token)

    def logout_session(self, token: str) -> None:
        """Invalidates an active session."""
        self._active_sessions.pop(token, None)


auth_manager = AuthSecurityManager()

