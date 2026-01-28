"""Password hashing utilities."""

import hashlib
import secrets


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a random salt."""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((salt + password).encode())
    return f"{salt}${hash_obj.hexdigest()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash."""
    try:
        salt, stored_hash = hashed.split('$')
        hash_obj = hashlib.sha256((salt + password).encode())
        return hash_obj.hexdigest() == stored_hash
    except (ValueError, AttributeError):
        return False
