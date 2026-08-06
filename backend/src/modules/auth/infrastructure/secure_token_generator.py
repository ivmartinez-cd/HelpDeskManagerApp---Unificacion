import hashlib
import secrets

_TOKEN_BYTES = 32


class SecureTokenGenerator:
    """Implementa el puerto SessionTokenGenerator. El mismo objeto sirve para
    tokens de sesión y de reset de password (ADR-004): ambos son "32 bytes
    aleatorios + sha256 para guardar", no hace falta un puerto separado."""

    def generate(self) -> str:
        return secrets.token_urlsafe(_TOKEN_BYTES)

    def hash(self, token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()
