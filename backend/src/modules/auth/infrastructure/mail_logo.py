"""Logo institucional para embeber en mails HTML como data URI (base64
inline) — mismo enfoque que `frontend/.../isotipo-mail-base64.ts`, evita
depender de que el cliente de mail cargue imágenes remotas o CID."""

import base64
from functools import lru_cache
from pathlib import Path

_LOGO_PATH = Path(__file__).parent / "assets" / "logo-canal-directo.png"


@lru_cache(maxsize=1)
def get_logo_base64() -> str:
    return base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")
