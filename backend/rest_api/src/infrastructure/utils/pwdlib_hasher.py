"""rest_api/src/infrastructure/utils/pwdlib_hasher.py."""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


class PwdlibHasher:
    """Password hasher implementation using pwdlib and Argon2."""

    def __init__(self) -> None:
        """Initialize hasher with Argon2 algorithm."""
        self._hasher = PasswordHash((Argon2Hasher(),))

    def hash(self, password: str) -> str:
        """Generate Argon2 hash."""
        return self._hasher.hash(password)

    def verify(self, password: str, hashed_password: str) -> bool:
        """Verify password against Argon2 hash."""
        return self._hasher.verify(password, hashed_password)
