"""El handler central traduce `IntegrityError` por SQLSTATE: duplicado -> 409,
referencia inexistente -> 404, borrado referenciado -> 409, check/not null -> 400,
desconocido -> 500 (ARCHITECTURE_GUIDE.md §6; ronda E2E 2026-09-05)."""

from sqlalchemy.exc import IntegrityError

from src.shared.presentation.errors.integrity import traducir_integrity_error


class _OrigAsyncpgError(Exception):
    """Imita el `orig` del adapter asyncpg de SQLAlchemy: `sqlstate` en el orig y
    la excepción real de asyncpg (con `constraint_name`) encadenada como causa."""

    def __init__(self, message: str, sqlstate: str, constraint: str | None = None) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate
        self.pgcode = sqlstate
        causa = Exception(message)
        causa.constraint_name = constraint  # type: ignore[attr-defined]
        self.__cause__ = causa


def _integrity(message: str, sqlstate: str, constraint: str | None = None) -> IntegrityError:
    return IntegrityError("INSERT ...", {}, _OrigAsyncpgError(message, sqlstate, constraint))


def test_unique_violation_es_409_conflicto() -> None:
    exc = _integrity("duplicate key value violates unique constraint", "23505", "x_key")
    status, code, _ = traducir_integrity_error(exc)
    assert (status, code) == (409, "CONFLICTO_DUPLICADO")


def test_fk_en_insert_es_404_referencia_inexistente() -> None:
    exc = _integrity(
        'insert or update on table "t" violates foreign key constraint "t_fk"', "23503", "t_fk"
    )
    status, code, _ = traducir_integrity_error(exc)
    assert (status, code) == (404, "REFERENCIA_INEXISTENTE")


def test_fk_en_delete_es_409_en_uso() -> None:
    exc = _integrity(
        'update or delete on table "t" violates foreign key constraint "h_fk" on table "h"',
        "23503",
        "h_fk",
    )
    status, code, _ = traducir_integrity_error(exc)
    assert (status, code) == (409, "EN_USO")


def test_check_y_not_null_son_400() -> None:
    for sqlstate in ("23514", "23502"):
        status, code, _ = traducir_integrity_error(_integrity("violates", sqlstate))
        assert (status, code) == (400, "VALIDATION_ERROR")


def test_sqlstate_desconocido_sigue_siendo_500() -> None:
    status, code, _ = traducir_integrity_error(_integrity("otra cosa", "23000"))
    assert (status, code) == (500, "INTERNAL_ERROR")


def test_sin_sqlstate_sigue_siendo_500() -> None:
    exc = IntegrityError("INSERT ...", {}, Exception("sin metadata"))
    status, _, _ = traducir_integrity_error(exc)
    assert status == 500
