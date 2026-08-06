from typing import Protocol


class SessionTokenGenerator(Protocol):
    """El token que va en la cookie es opaco (ADR-004): esto lo genera y lo
    reduce a lo único que se persiste (su hash)."""

    def generate(self) -> str: ...
    def hash(self, token: str) -> bytes: ...
