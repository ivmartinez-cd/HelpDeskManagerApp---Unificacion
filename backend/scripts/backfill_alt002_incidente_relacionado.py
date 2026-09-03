"""Backfill de `alertas.incidente_relacionado_id` para ALT002 ya gestionadas
antes de que ese campo existiera (commit 3f44627, sin backfill de datos).

El campo lo carga la TL a mano desde el modal — acá no hay forma de "adivinar"
la ruta compartida para las ALT002 sin texto (26/33 dicen solo "Km asociado a
otro incidente", sin número), así que el criterio es: parsear en
`alertas.justificacion` una referencia numérica de 5 a 7 dígitos a otro
`incidentes.numero_incidente` (medido 2026-09-03 contra la DB real: patrones
como "Se suma al recorrido el caso 842755" o "Recorrido completo con el caso
843600"), resolverla contra los incidentes de la MISMA liquidación (mismo
requisito que valida `ActualizarEstadoAlerta`) y vincular solo si aparece un
único incidente candidato distinto del dueño de la alerta. Todo lo demás
(sin número, número no encontrado en la liquidación, o más de un candidato
distinto) queda en NULL y se lista para revisión manual desde el modal.

Uso (parado en `backend/`, dentro del contenedor):
  uv run python scripts/backfill_alt002_incidente_relacionado.py --dry-run   # solo lista
  uv run python scripts/backfill_alt002_incidente_relacionado.py            # persiste

Sin --dry-run escribe en la DB real de la instancia (DATABASE_URL del .env local).
"""

import argparse
import asyncio
import re
from collections import defaultdict
from uuid import UUID

from sqlalchemy import select

from src.modules.liquidaciones.infrastructure.models.alerta_model import AlertaModel
from src.modules.liquidaciones.infrastructure.models.incidente_model import IncidenteModel
from src.modules.liquidaciones.infrastructure.models.liquidacion_model import (  # noqa: F401
    LiquidacionModel,
)
from src.modules.liquidaciones.infrastructure.repositories.sqlalchemy_alerta_repository import (
    SqlAlchemyAlertaRepository,
)
from src.shared.infrastructure.database.session import get_sessionmaker

_REF_NUMERO = re.compile(r"\b\d{5,7}\b")


class _Candidatos:
    def __init__(self) -> None:
        self.actualizadas = 0
        self.sin_referencia: list[str] = []
        self.sin_match: list[str] = []
        self.ambiguas: list[str] = []


async def _run(dry_run: bool) -> None:
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        alertas_stmt = select(AlertaModel).where(
            AlertaModel.tipo_alerta == "ALT002",
            AlertaModel.justificacion.is_not(None),
            AlertaModel.incidente_relacionado_id.is_(None),
        )
        alertas = (await session.execute(alertas_stmt)).scalars().all()
        print(f"ALT002 con justificación y sin vínculo: {len(alertas)}")
        if not alertas:
            return

        liquidacion_ids = {a.liquidacion_id for a in alertas}
        incidentes_por_liq: dict[UUID, dict[str, list[IncidenteModel]]] = {}
        for liq_id in liquidacion_ids:
            incidentes = (
                (
                    await session.execute(
                        select(IncidenteModel).where(IncidenteModel.liquidacion_id == liq_id)
                    )
                )
                .scalars()
                .all()
            )
            por_numero: dict[str, list[IncidenteModel]] = defaultdict(list)
            for inc in incidentes:
                por_numero[inc.numero_incidente].append(inc)
            incidentes_por_liq[liq_id] = por_numero

        alerta_repo = SqlAlchemyAlertaRepository(session)
        resultado = _Candidatos()

        for alerta in alertas:
            dueno = next(
                (
                    inc
                    for lista in incidentes_por_liq[alerta.liquidacion_id].values()
                    for inc in lista
                    if inc.id == alerta.incidente_id
                ),
                None,
            )
            numero_dueno = dueno.numero_incidente if dueno else None
            referencias = {
                n for n in _REF_NUMERO.findall(alerta.justificacion) if n != numero_dueno
            }
            if not referencias:
                resultado.sin_referencia.append(_describir(alerta, numero_dueno))
                continue

            candidatos_ids = {
                inc.id
                for numero in referencias
                for inc in incidentes_por_liq[alerta.liquidacion_id].get(numero, [])
            }
            if not candidatos_ids:
                resultado.sin_match.append(
                    f"{_describir(alerta, numero_dueno)} refs={sorted(referencias)}"
                )
                continue
            if len(candidatos_ids) > 1:
                resultado.ambiguas.append(
                    f"{_describir(alerta, numero_dueno)} refs={sorted(referencias)}"
                )
                continue

            (incidente_relacionado_id,) = candidatos_ids
            print(
                f"  VINCULA alerta={alerta.id} incidente={numero_dueno} "
                f"justificacion={alerta.justificacion!r} -> "
                f"incidente_relacionado={incidente_relacionado_id}"
            )
            if not dry_run:
                await alerta_repo.update_estado(
                    alerta.liquidacion_id,
                    alerta.id,
                    estado=alerta.estado,
                    justificacion=alerta.justificacion,
                    incidente_relacionado_id=incidente_relacionado_id,
                )
            resultado.actualizadas += 1

        if not dry_run:
            await session.commit()

        print(f"\n{'(dry-run) ' if dry_run else ''}vinculadas={resultado.actualizadas}")
        _listar("sin referencia numérica en la justificación", resultado.sin_referencia)
        _listar("referencia no encontrada en la misma liquidación", resultado.sin_match)
        _listar("ambiguas (más de un incidente candidato)", resultado.ambiguas)


def _describir(alerta: AlertaModel, numero_dueno: str | None) -> str:
    return f"alerta={alerta.id} incidente={numero_dueno} justificacion={alerta.justificacion!r}"


def _listar(titulo: str, items: list[str]) -> None:
    print(f"\n{titulo} ({len(items)}):")
    for item in items:
        print(f"  {item}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, no persiste")
    args = parser.parse_args()
    asyncio.run(_run(args.dry_run))


if __name__ == "__main__":
    main()
