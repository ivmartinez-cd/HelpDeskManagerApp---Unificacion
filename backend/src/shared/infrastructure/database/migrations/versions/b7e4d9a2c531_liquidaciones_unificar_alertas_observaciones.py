"""liquidaciones unificar alertas y observaciones

Unifica dos entidades casi idénticas del motor de reglas — `Alerta` (1:1 con un
incidente) y `Observacion` (agrupaba N incidentes, sin justificación
obligatoria, vocabulario de estados propio) — en una sola tabla `alertas`
(auditoría de liquidaciones, hallazgo "Alertas vs. Observaciones — dos
máquinas de estado parecidas"). Hoy solo lo genera ALT005 agrupando por
corredor; el resto de las reglas siguen siendo 1:1 (`es_grupo=False`).

Verificado antes de escribir esto: las 754 filas reales de `observaciones`
están el 100% en estado "pendiente" (0 triageadas) — no hay ningún trabajo de
la TL que se pueda perder al migrar. Los 32.754 registros reales de `alertas`
no se tocan de forma destructiva, solo ganan columnas nuevas (nullable).

Migración de datos:
- Agrega a `alertas`: `es_grupo` (default false), `monto_cobrado`,
  `monto_esperado`, `diferencia` (nullable — solo se completan para
  `es_grupo=True`).
- Crea `alerta_incidentes` (ex `observacion_incidentes`): incidentes de una
  alerta agrupada, con `rol` principal/referencia.
- Por cada `observaciones` (siempre `regla_codigo='ALT005'`, verificado):
  crea una `alertas` con `incidente_id` = el incidente `rol='principal'` de
  `observacion_incidentes` (las 754 filas reales tienen exactamente uno — 2+
  o 0 aborta la migración en vez de adivinar), `descripcion` = título +
  descripción combinados (mismo formato que ahora arma
  `alt005_ruta.py::_crear_alerta_grupo`), `riesgo` = severidad mapeada a la
  escala numérica ya vigente (CRITICO=90, ADVERTENCIA=50, INFORMATIVO=20;
  fallback 60 para cualquier otro valor no visto en el dry-run), `estado` =
  el de Observacion salvo `rechazada`→`descartada` y
  `excepcion_aprobada`→`resuelta` (ningún registro real usa estos dos hoy).
- Copia `observacion_incidentes` a `alerta_incidentes` con el nuevo id de
  alerta.
- Borra `observacion_incidentes` y `observaciones`.

Revision ID: b7e4d9a2c531
Revises: afeba4493f74
Create Date: 2026-09-04 21:50:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e4d9a2c531"
down_revision: str | None = "afeba4493f74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RIESGO_POR_SEVERIDAD = {"CRITICO": 90.0, "ADVERTENCIA": 50.0, "INFORMATIVO": 20.0}
_ESTADO_MAP = {"rechazada": "descartada", "excepcion_aprobada": "resuelta"}

_observaciones = sa.table(
    "observaciones",
    sa.column("id", sa.UUID),
    sa.column("liquidacion_id", sa.UUID),
    sa.column("tipo_observacion", sa.String),
    sa.column("severidad", sa.String),
    sa.column("titulo", sa.String),
    sa.column("descripcion", sa.String),
    sa.column("datos_contexto", sa.JSON),
    sa.column("monto_cobrado", sa.Float),
    sa.column("monto_esperado", sa.Float),
    sa.column("diferencia", sa.Float),
    sa.column("estado", sa.String),
    sa.column("regla_codigo", sa.String),
    sa.column("fecha_generacion", sa.DateTime(timezone=True)),
)
_observacion_incidentes = sa.table(
    "observacion_incidentes",
    sa.column("id", sa.UUID),
    sa.column("observacion_id", sa.UUID),
    sa.column("incidente_id", sa.UUID),
    sa.column("rol", sa.String),
)
_alertas = sa.table(
    "alertas",
    sa.column("id", sa.UUID),
    sa.column("incidente_id", sa.UUID),
    sa.column("liquidacion_id", sa.UUID),
    sa.column("tipo_alerta", sa.String),
    sa.column("descripcion", sa.String),
    sa.column("datos_contexto", sa.JSON),
    sa.column("riesgo", sa.Float),
    sa.column("estado", sa.String),
    sa.column("fecha_generacion", sa.DateTime(timezone=True)),
    sa.column("es_grupo", sa.Boolean),
    sa.column("monto_cobrado", sa.Float),
    sa.column("monto_esperado", sa.Float),
    sa.column("diferencia", sa.Float),
)
_alerta_incidentes = sa.table(
    "alerta_incidentes",
    sa.column("id", sa.UUID),
    sa.column("alerta_id", sa.UUID),
    sa.column("incidente_id", sa.UUID),
    sa.column("rol", sa.String),
)


def upgrade() -> None:
    bind = op.get_bind()
    _agregar_columnas_alertas()
    _crear_tabla_alerta_incidentes()
    _migrar_observaciones(bind)
    op.drop_table("observacion_incidentes")
    op.drop_table("observaciones")


def _agregar_columnas_alertas() -> None:
    op.add_column(
        "alertas",
        sa.Column("es_grupo", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("alertas", sa.Column("monto_cobrado", sa.Float(), nullable=True))
    op.add_column("alertas", sa.Column("monto_esperado", sa.Float(), nullable=True))
    op.add_column("alertas", sa.Column("diferencia", sa.Float(), nullable=True))


def _crear_tabla_alerta_incidentes() -> None:
    op.create_table(
        "alerta_incidentes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "alerta_id",
            sa.UUID(),
            sa.ForeignKey("alertas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "incidente_id",
            sa.UUID(),
            sa.ForeignKey("incidentes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rol", sa.String(), nullable=False, server_default="referencia"),
    )


def _migrar_observaciones(bind: sa.Connection) -> None:
    for obs in bind.execute(sa.select(_observaciones)).fetchall():
        principal_id = _incidente_principal(bind, obs.id)
        alerta_id = uuid.uuid4()
        bind.execute(
            _alertas.insert().values(
                id=alerta_id,
                incidente_id=principal_id,
                liquidacion_id=obs.liquidacion_id,
                tipo_alerta=obs.regla_codigo or "ALT005",
                descripcion=f"{obs.titulo}. {obs.descripcion}" if obs.descripcion else obs.titulo,
                datos_contexto=obs.datos_contexto,
                riesgo=_RIESGO_POR_SEVERIDAD.get(obs.severidad, 60.0),
                estado=_ESTADO_MAP.get(obs.estado, obs.estado),
                fecha_generacion=obs.fecha_generacion,
                es_grupo=True,
                monto_cobrado=obs.monto_cobrado,
                monto_esperado=obs.monto_esperado,
                diferencia=obs.diferencia,
            )
        )
        _migrar_vinculos(bind, obs.id, alerta_id)


def _incidente_principal(bind: sa.Connection, observacion_id: uuid.UUID) -> uuid.UUID:
    principales = bind.execute(
        sa.select(_observacion_incidentes.c.incidente_id).where(
            _observacion_incidentes.c.observacion_id == observacion_id,
            _observacion_incidentes.c.rol == "principal",
        )
    ).fetchall()
    if len(principales) != 1:
        raise RuntimeError(
            f"Migración observaciones->alertas: observacion {observacion_id} tiene "
            f"{len(principales)} incidentes 'principal' (se esperaba exactamente 1) — "
            "caso no visto en el dry-run, revisar a mano antes de continuar."
        )
    return principales[0].incidente_id


def _migrar_vinculos(bind: sa.Connection, observacion_id: uuid.UUID, alerta_id: uuid.UUID) -> None:
    vinculos = bind.execute(
        sa.select(_observacion_incidentes.c.incidente_id, _observacion_incidentes.c.rol).where(
            _observacion_incidentes.c.observacion_id == observacion_id
        )
    ).fetchall()
    bind.execute(
        _alerta_incidentes.insert(),
        [
            {
                "id": uuid.uuid4(),
                "alerta_id": alerta_id,
                "incidente_id": v.incidente_id,
                "rol": v.rol,
            }
            for v in vinculos
        ],
    )


def downgrade() -> None:
    # Irreversible a propósito: no hay forma de reconstruir qué filas de
    # `alertas` originalmente eran `Observacion` una vez borradas las tablas
    # viejas. Restaurar desde el backup pre-migración si hace falta volver.
    raise RuntimeError("Downgrade no soportado — restaurar desde backup pre-migración.")
