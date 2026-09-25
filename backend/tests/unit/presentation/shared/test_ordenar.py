from dataclasses import dataclass

from src.shared.presentation.schemas.ordenar import ordenar_por_campo


@dataclass
class _Fila:
    id: int
    cliente: str
    dias: int | None


_FILAS = [_Fila(1, "banco", 5), _Fila(2, "Arcor", None), _Fila(3, "Coto", 9), _Fila(4, "arcor", 5)]


def _ids(filas: list[_Fila]) -> list[int]:
    return [f.id for f in filas]


def test_sin_campo_respeta_el_orden_de_llegada() -> None:
    assert _ids(ordenar_por_campo(_FILAS, None, "desc")) == [1, 2, 3, 4]


def test_texto_sin_distinguir_mayusculas_y_empates_en_orden_de_llegada() -> None:
    assert _ids(ordenar_por_campo(_FILAS, "cliente", "asc")) == [2, 4, 1, 3]
    assert _ids(ordenar_por_campo(_FILAS, "cliente", "desc")) == [3, 1, 2, 4]


def test_vacios_al_final_en_ambos_sentidos() -> None:
    assert _ids(ordenar_por_campo(_FILAS, "dias", "asc")) == [1, 4, 3, 2]
    assert _ids(ordenar_por_campo(_FILAS, "dias", "desc")) == [3, 1, 4, 2]
