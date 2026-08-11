"""Dígito verificador y formato visible de los IDs de supply de Canal Directo."""


def ean_check_digit(number: str | int) -> int:
    """Módulo-10 propio de Canal Directo: pesos 3,1,3,1,... aplicados de IZQUIERDA a
    derecha — no desde el dígito más a la derecha como el EAN/GTIN estándar. Fácil de
    implementar mal si se asume el algoritmo estándar por el nombre."""
    digits = [int(d) for d in str(number)]
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(digits))
    return (10 - total % 10) % 10


def supply_id_full(supply_id: int) -> str:
    """Formato con el que el portal muestra un pedido: "{id}-{dígito}" (ej. "441415-9")."""
    return f"{supply_id}-{ean_check_digit(supply_id)}"
