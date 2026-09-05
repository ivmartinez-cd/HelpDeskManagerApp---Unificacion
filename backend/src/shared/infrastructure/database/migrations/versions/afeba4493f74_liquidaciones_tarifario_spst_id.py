"""liquidaciones tarifario spst_id

Refactor de fondo (no solo un rename): `Tarifario.zona` (texto libre, tenía que
matchear letra por letra con `Spst.zona`) se reemplaza por `Tarifario.spst_id`
(FK real). Verificado contra la base real antes de escribir esto (dry-run
2026-09-04): en TODO el sistema no hay un solo caso de una `zona` de Tarifario
compartida por más de un SPST del mismo prestador — la "zona" siempre fue, en
los hechos, un alias 1 a 1 de un SPST puntual. Motivo completo: ver la sesión
de refactor de liquidaciones del 2026-09-04.

`Spst.zona` se renombra a `zona_cobertura` — sigue existiendo, pero ahora es
inequívocamente solo un texto de ayuda para que "Vincular SPST" sugiera
coincidencias por localidad; ya no tiene ningún efecto sobre qué tarifa se le
cobra a un incidente.

`tarifario_zona_maps.zona_local` (texto) pasa a `spst_id` (FK) — mismo
criterio: el sync de Siges (ADR-014) crea tarifarios apuntando a un SPST, no a
una zona de texto.

Migración de datos (verificada antes de escribir, sin casos ambiguos):
- zona IS NULL -> spst_id NULL (genérica, mismo comportamiento).
- zona con exactamente 1 SPST candidato del mismo prestador -> ese spst_id.
- zona sin ningún SPST candidato -> la fila queda huérfana desde antes de esta
  migración (ya era inalcanzable: sin SPST no hay forma de que el motor la
  resuelva) — se borra, mismo criterio ya aplicado a mano en INFOMAC el
  2026-09-04. Si esta migración corre contra una base con un caso ambiguo (2+
  SPST candidatos) que el dry-run no vio, aborta en vez de adivinar.

Revision ID: afeba4493f74
Revises: f2a9c4e8b1d6
Create Date: 2026-09-04 20:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "afeba4493f74"
down_revision: str | None = "f2a9c4e8b1d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_tarifarios = sa.table(
    "tarifarios",
    sa.column("id", sa.UUID),
    sa.column("prestador_id", sa.UUID),
    sa.column("zona", sa.String),
    sa.column("spst_id", sa.UUID),
)
_spsts = sa.table(
    "spsts",
    sa.column("id", sa.UUID),
    sa.column("prestador_id", sa.UUID),
    sa.column("zona", sa.String),
)
_maps = sa.table(
    "tarifario_zona_maps",
    sa.column("id", sa.UUID),
    sa.column("prestador_id", sa.UUID),
    sa.column("zona_local", sa.String),
    sa.column("spst_id", sa.UUID),
)


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column("tarifarios", sa.Column("spst_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "tarifarios_spst_id_fkey", "tarifarios", "spsts", ["spst_id"], ["id"], ondelete="SET NULL"
    )
    _migrar_zona_a_spst(bind, _tarifarios, "zona")
    _borrar_huerfanas(bind)
    op.drop_column("tarifarios", "zona")

    op.add_column("tarifario_zona_maps", sa.Column("spst_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "tarifario_zona_maps_spst_id_fkey",
        "tarifario_zona_maps",
        "spsts",
        ["spst_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # Todavía referencia `spsts.zona` (sin renombrar) — el rename va al final,
    # después de que las dos migraciones de datos ya lo necesitaron.
    _migrar_zona_a_spst(bind, _maps, "zona_local")
    op.drop_column("tarifario_zona_maps", "zona_local")

    op.alter_column("spsts", "zona", new_column_name="zona_cobertura")


def _migrar_zona_a_spst(bind: sa.Connection, tabla: sa.Table, columna_zona: str) -> None:
    """zona IS NULL ya queda spst_id NULL (default) sin tocar nada. Para el
    resto, agrupa por (prestador_id, zona) una sola vez y exige un único
    candidato — más de uno aborta la migración en vez de adivinar."""
    zona_col = tabla.c[columna_zona]
    filas = bind.execute(
        sa.select(tabla.c.prestador_id, zona_col).where(zona_col.isnot(None)).distinct()
    ).fetchall()
    for prestador_id, zona in filas:
        candidatos = bind.execute(
            sa.select(_spsts.c.id).where(
                _spsts.c.prestador_id == prestador_id, _spsts.c.zona == zona
            )
        ).fetchall()
        if len(candidatos) > 1:
            raise RuntimeError(
                f"Migración tarifario->spst_id: zona '{zona}' del prestador {prestador_id} "
                f"matchea {len(candidatos)} SPST — caso ambiguo no visto en el dry-run, "
                "revisar a mano antes de continuar."
            )
        if len(candidatos) == 1:
            bind.execute(
                tabla.update()
                .where(tabla.c.prestador_id == prestador_id, zona_col == zona)
                .values(spst_id=candidatos[0].id)
            )


def _borrar_huerfanas(bind: sa.Connection) -> None:
    """Tarifarios cuya zona no matcheó ningún SPST: ya eran inalcanzables antes
    de esta migración (sin SPST el motor nunca las resuelve) — mismo criterio
    ya aplicado a mano en INFOMAC. Verificado en el dry-run: 14 filas en todo
    el sistema (CDU y TANDIL, ninguno de los dos con SPST configurado)."""
    bind.execute(
        _tarifarios.delete().where(
            _tarifarios.c.zona.isnot(None), _tarifarios.c.spst_id.is_(None)
        )
    )


def downgrade() -> None:
    # Irreversible a propósito: las filas huérfanas borradas y el texto de
    # zona original no se pueden reconstruir desde spst_id (relación N:1
    # perdida). Restaurar desde el backup pre-migración si hace falta volver.
    raise RuntimeError("Downgrade no soportado — restaurar desde backup pre-migración.")
