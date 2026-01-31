"""Password hashing utilities using PBKDF2-HMAC-SHA256."""

import hashlib
import hmac
import secrets


# PBKDF2 configuration
_HASH_ALGORITHM = "sha256"
_ITERATIONS = 600_000
_SALT_LENGTH = 32
_KEY_LENGTH = 32


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt.

    Args:
        password: The plaintext password to hash.

    Returns:
        A string in the format 'salt$iterations$hash' (all hex-encoded).
    """
    salt = secrets.token_bytes(_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac(
        _HASH_ALGORITHM, password.encode(), salt, _ITERATIONS, dklen=_KEY_LENGTH
    )
    return f"{salt.hex()}${_ITERATIONS}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a PBKDF2 hash.

    Args:
        password: The plaintext password to verify.
        hashed: The stored hash string from hash_password().

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        salt_hex, iterations_str, stored_hash = hashed.split('$')
        salt = bytes.fromhex(salt_hex)
        iterations = int(iterations_str)
        dk = hashlib.pbkdf2_hmac(
            _HASH_ALGORITHM, password.encode(), salt, iterations, dklen=_KEY_LENGTH
        )
        return hmac.compare_digest(dk.hex(), stored_hash)
    except (ValueError, AttributeError):
        return False
