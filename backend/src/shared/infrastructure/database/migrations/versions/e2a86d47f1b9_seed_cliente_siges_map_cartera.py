"""Seed 2 del mapa cliente de Gestión → Empresa(s) de Siges.

Al pasar la card de "clientes del mes" a "cartera" (ventana futura completa
del calendario, para matchear la planilla de cuentas por operador de la TL),
aparecieron 11 clientes más sin cruce (eventos de sep-nov 2026). Mapeados a
mano por el usuario el 2026-08-14 con candidatos reales de Siges a la vista.

Revision ID: e2a86d47f1b9
Revises: c7e4b19f8a35
Create Date: 2026-08-14
"""

import sqlalchemy as sa
from alembic import op

revision = "e2a86d47f1b9"
down_revision = "c7e4b19f8a35"
branch_labels = None
depends_on = None

# (cliente en Gestión, [ID_Empresa de Siges, ...])
_ALIAS: list[tuple[str, list[int]]] = [
    ("ADM Agro (Alfred Toepfer)", [125]),  # ADM Agro S.R.L
    ("Arcos Dorados", [634, 790]),  # Mc Donalds + La Casa de Ronald McDonald
    ("IEASA", [1036]),  # ENARSA (Energía Argentina S.A., confirmado por el usuario)
    ("Laboratorio Andromaco", [757, 763]),  # Laboratorios Andromaco + Proximitas
    ("Molino Cañuelas / Tiendas Gourmet", [515, 824]),
    ("PETROLERA SANTA MARIA | PSM - ENAP SIPETROL", [667]),  # Enap Sipetrol - YPF
    ("Plastiferro", [1105]),  # desambigua el duplicado con 379
    ("Rheem/Finpak", [73]),  # Rheem (Finpak 517 quedó afuera a pedido del usuario)
    ("Telered / Ver TV", [528]),  # Ver TV (Telered 110 quedó afuera)
    ("Violetta Fabbiani", [28]),  # 'Violetta Fabiani' — ortografía distinta en Siges
    ("Vitamina (Tiendas Gourmet)", [824]),  # Tiendas Gourmet
]

_tabla = sa.table(
    "contadores_cliente_siges_map",
    sa.column("cliente_gestion", sa.String),
    sa.column("siges_empresa_id", sa.Integer),
)


def upgrade() -> None:
    filas = [
        {"cliente_gestion": cliente, "siges_empresa_id": empresa_id}
        for cliente, empresa_ids in _ALIAS
        for empresa_id in empresa_ids
    ]
    op.bulk_insert(_tabla, filas)


def downgrade() -> None:
    clientes = [cliente for cliente, _ in _ALIAS]
    op.execute(
        _tabla.delete().where(_tabla.c.cliente_gestion.in_(clientes))
    )
