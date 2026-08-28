"""Seed 3 del mapa cliente de Gestión → Empresa(s) de Siges: Galeno.

"Galeno" en Gestión es un solo cliente, pero en Siges son 11 empresas
separadas por sede/razón social ("Galeno - Sanatorio Trinidad Mitre", etc.).
El cruce automático (`cliente_matcher.match_clientes`) resuelve al exacto
único ("Galeno", id 119) y nunca llega a la contención — las otras 10 sedes
quedaban huérfanas (298 equipos "Sin operador asignado" en el universo de
`equipos_sin_real`, 10 de ellos de Galeno), detectado 2026-08-28 al revisar
el desglose por operador. Confirmado con el usuario el mismo día: se incluyen
las 10 sedes de salud, se excluye "GALENO SEGUROS S.A." (893) por ser un
rubro distinto (aseguradora, no la cadena de sanatorios).

Revision ID: 13b8777b84d0
Revises: 73be3bdccdf5
Create Date: 2026-08-28
"""

import sqlalchemy as sa
from alembic import op

revision = "13b8777b84d0"
down_revision = "73be3bdccdf5"
branch_labels = None
depends_on = None

# (cliente en Gestión, [ID_Empresa de Siges, ...])
_ALIAS: list[tuple[str, list[int]]] = [
    (
        "Galeno",
        [
            119,  # Galeno
            961,  # Galeno - Centro Médico Barrio Norte
            646,  # Galeno - COLONOS
            933,  # Galeno - Sanatorio Trinidad Mitre
            1231,  # Galeno - Sanatorio Trinidad Neuquén
            934,  # Galeno - Sanatorio Trinidad Palermo
            120,  # Galeno - Sanatorio Trinidad Quilmes
            936,  # Galeno - Sanatorio Trinidad Ramos Mejia
            935,  # Galeno - Sanatorio Trinidad San Isidro Fleming
            962,  # Galeno - Trinidad San Isidro Thames
        ],
    ),
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
