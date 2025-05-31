"""User authentication utilities."""

from dataclasses import dataclass
import hashlib
import os
import base64


@dataclass
class User:
    """User account information."""

    id: int | None
    username: str
    password_hash: str
    salt: str

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        salt_bytes = base64.b64decode(self.salt)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, 100000)
        return base64.b64encode(hashed).decode() == self.password_hash

    @staticmethod
    def hash_password(password: str) -> tuple[str, str]:
        """Create a password hash and salt for storage."""
        salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return (
            base64.b64encode(hashed).decode(),
            base64.b64encode(salt).decode(),
        )

    @classmethod
    def create(cls, username: str, password: str) -> "User":
        """Create a new ``User`` instance from plaintext password."""
        password_hash, salt = cls.hash_password(password)
        return cls(id=None, username=username, password_hash=password_hash, salt=salt)


# Module-level wrapper functions for backward compatibility
def hash_password(password: str) -> tuple[str, str]:
    """Create a password hash and salt for storage."""
    return User.hash_password(password)


def verify_password(user: User, password: str) -> bool:
    """Verify a password against the stored hash."""
    return user.verify_password(password)
