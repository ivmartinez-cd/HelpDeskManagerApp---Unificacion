"""insumos despachados schema

Revision ID: f2c7a9d4b1e8
Revises: e5a9c3d7b1f4
Create Date: 2026-09-24 00:00:00.000000

Insumos > Despachados: seguimiento en OCA de los remitos de insumos despachados. Todo vive
en la base de HDM; Siges y OCA solo se leen. Seis tablas con prefijo `insumos_despacho_`
(para no confundirlas con `dismissed_supplies`/`dispatch_unconfirmed_notifications`, que
son de pedidos de Canal Directo):

- `envio`: una fila por guía OCA, con el último estado leído de OCA (columnas `oca_*`,
  NULL mientras OCA no la registre), la clasificación del semáforo que calcula el job y el
  cierre manual de la alerta. El color se guarda (no se calcula al leer) para poder filtrar
  y paginar en SQL; lo recalcula cada corrida del job.
- `remito` e `incidente`: de dónde sale la guía en Siges. Una guía puede venir en más de
  un remito y un remito puede llevar varios pedidos de insumos. `id_remito` es el
  `Remito_Cab.Id_Remito` de Siges (BIGINT natural, criterio de insumos para IDs externos).
- `estado_historial`: cada cambio de estado que el job observa (no la historia completa de
  OCA: `GetEnvioEstadoActual` solo devuelve el estado actual).
- `accion`: lo que registra el operador desde "Registrar acción". Solo se agregan filas.
- `corrida`: cada ejecución del job (programada o "Actualizar ahora"), para mostrar la
  última consulta a OCA y el avance de una corrida manual.

Los usuarios se guardan con FK a `app_user` (ON DELETE SET NULL) más el nombre
denormalizado, para que el registro sobreviva a la baja del usuario.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "f2c7a9d4b1e8"
down_revision: str | None = "e5a9c3d7b1f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLORES = "('verde', 'amarillo', 'naranja', 'rojo', 'gris', 'cerrado')"


def _creado_en(nombre: str = "creado_en") -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        nombre, sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
    )


def _usuario_fk(nombre: str) -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(nombre, UUID(as_uuid=True), sa.ForeignKey("app_user.id", ondelete="SET NULL"))


def _guia_fk() -> sa.Column:  # type: ignore[type-arg]
    return sa.Column(
        "guia",
        sa.String(19),
        sa.ForeignKey("insumos_despacho_envio.guia", ondelete="CASCADE"),
        nullable=False,
    )


def _crear_envio() -> None:
    op.create_table(
        "insumos_despacho_envio",
        sa.Column("guia", sa.String(19), primary_key=True),
        sa.Column("id_distribucion", sa.Integer(), nullable=False),
        sa.Column("fecha_remito", sa.Date(), nullable=False),
        sa.Column("cliente", sa.String(), nullable=False, server_default=""),
        sa.Column("sucursal_cliente", sa.String(), nullable=False, server_default=""),
        sa.Column("oca_id_estado", sa.Integer(), nullable=True),
        sa.Column("oca_estado", sa.String(), nullable=True),
        sa.Column("oca_motivo", sa.String(), nullable=True),
        sa.Column("oca_sucursal", sa.String(), nullable=True),
        sa.Column("oca_fecha_estado", sa.Date(), nullable=True),
        sa.Column("oca_operativa", sa.String(), nullable=True),
        sa.Column("oca_orden_retiro", sa.String(), nullable=True),
        sa.Column("oca_cantidad_paquetes", sa.Integer(), nullable=True),
        sa.Column("color", sa.String(10), nullable=False),
        sa.Column("alerta", sa.Boolean(), nullable=False),
        sa.Column("abierto", sa.Boolean(), nullable=False),
        sa.Column("fecha_limite", sa.Date(), nullable=True),
        sa.Column("observacion", sa.String(), nullable=False, server_default=""),
        sa.Column("estado_desconocido", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consultado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_error", sa.String(), nullable=True),
        sa.Column("ultimo_error_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("alerta_cerrada_en", sa.DateTime(timezone=True), nullable=True),
        _usuario_fk("alerta_cerrada_por_id"),
        sa.Column("alerta_cerrada_por_nombre", sa.String(), nullable=True),
        _creado_en(),
        _creado_en("actualizado_en"),
        sa.CheckConstraint(f"color IN {_COLORES}", name="ck_insumos_despacho_envio_color"),
    )
    op.create_index("ix_insumos_despacho_envio_abierto", "insumos_despacho_envio", ["abierto"])
    op.create_index("ix_insumos_despacho_envio_color", "insumos_despacho_envio", ["color"])
    op.create_index(
        "ix_insumos_despacho_envio_fecha_remito", "insumos_despacho_envio", ["fecha_remito"]
    )


def _crear_remito_e_incidente() -> None:
    op.create_table(
        "insumos_despacho_remito",
        sa.Column("id_remito", sa.BigInteger(), primary_key=True, autoincrement=False),
        _guia_fk(),
        sa.Column("numero_remito", sa.BigInteger(), nullable=False),
        sa.Column("fecha_remito", sa.Date(), nullable=False),
        sa.Column("bultos", sa.Integer(), nullable=False),
        sa.Column("id_distribucion", sa.Integer(), nullable=False),
        sa.Column("cliente", sa.String(), nullable=False, server_default=""),
        sa.Column("sucursal_cliente", sa.String(), nullable=False, server_default=""),
        sa.Column("entrega_a", sa.String(), nullable=False, server_default=""),
        _creado_en(),
    )
    op.create_index("ix_insumos_despacho_remito_guia", "insumos_despacho_remito", ["guia"])
    op.create_index(
        "ix_insumos_despacho_remito_numero", "insumos_despacho_remito", ["numero_remito"]
    )
    op.create_table(
        "insumos_despacho_incidente",
        sa.Column(
            "id_remito",
            sa.BigInteger(),
            sa.ForeignKey("insumos_despacho_remito.id_remito", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("numero", sa.String(13), primary_key=True),
        sa.Column("numero_cliente", sa.String(), nullable=False, server_default=""),
    )
    op.create_index(
        "ix_insumos_despacho_incidente_numero", "insumos_despacho_incidente", ["numero"]
    )


def _crear_historial_y_acciones() -> None:
    op.create_table(
        "insumos_despacho_estado_historial",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        _guia_fk(),
        sa.Column("id_estado", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(), nullable=False),
        sa.Column("motivo", sa.String(), nullable=False),
        sa.Column("sucursal", sa.String(), nullable=False),
        sa.Column("fecha_estado", sa.Date(), nullable=False),
        sa.Column("color", sa.String(10), nullable=False),
        _creado_en("observado_en"),
        sa.CheckConstraint(
            f"color IN {_COLORES}", name="ck_insumos_despacho_estado_historial_color"
        ),
    )
    op.create_index(
        "ix_insumos_despacho_estado_historial_guia",
        "insumos_despacho_estado_historial",
        ["guia", "observado_en"],
    )
    op.create_table(
        "insumos_despacho_accion",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        _guia_fk(),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=False),
        sa.Column("resultado", sa.String(20), nullable=False),
        sa.Column("cerro_alerta", sa.Boolean(), nullable=False, server_default=sa.false()),
        _usuario_fk("usuario_id"),
        sa.Column("usuario_nombre", sa.String(), nullable=False),
        _creado_en("creada_en"),
        sa.CheckConstraint(
            "tipo IN ('llamado_cliente', 'mail_cliente', 'reclamo_oca', 'otro')",
            name="ck_insumos_despacho_accion_tipo",
        ),
        sa.CheckConstraint(
            "resultado IN ('resuelto', 'pendiente', 'sin_respuesta')",
            name="ck_insumos_despacho_accion_resultado",
        ),
    )
    op.create_index(
        "ix_insumos_despacho_accion_guia", "insumos_despacho_accion", ["guia", "creada_en"]
    )


def _crear_corrida() -> None:
    op.create_table(
        "insumos_despacho_corrida",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("origen", sa.String(12), nullable=False),
        _creado_en("iniciada_en"),
        sa.Column("terminada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usuario_nombre", sa.String(), nullable=True),
        sa.Column("envios_nuevos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consultas_ok", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("consultas_error", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.String(), nullable=True),
        sa.CheckConstraint(
            "origen IN ('programada', 'manual')", name="ck_insumos_despacho_corrida_origen"
        ),
    )
    op.create_index(
        "ix_insumos_despacho_corrida_iniciada_en", "insumos_despacho_corrida", ["iniciada_en"]
    )


def upgrade() -> None:
    _crear_envio()
    _crear_remito_e_incidente()
    _crear_historial_y_acciones()
    _crear_corrida()


def downgrade() -> None:
    # El orden inverso respeta las FK; drop_table se lleva índices y checks.
    for tabla in (
        "insumos_despacho_corrida",
        "insumos_despacho_accion",
        "insumos_despacho_estado_historial",
        "insumos_despacho_incidente",
        "insumos_despacho_remito",
        "insumos_despacho_envio",
    ):
        op.drop_table(tabla)
