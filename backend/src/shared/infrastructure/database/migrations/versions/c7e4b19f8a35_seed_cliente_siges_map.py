"""Seed del mapa cliente de Gestión → Empresa(s) de Siges.

Los 28 clientes del calendario de Contadores que el cruce automático no
resolvía (agosto 2026), mapeados a mano por el usuario el 2026-08-14 con
candidatos reales de Siges a la vista. Los compuestos ('Salta Refrescos',
'Grupo Randazzo', etc.) tienen varias filas: el cliente suma esas empresas.

Revision ID: c7e4b19f8a35
Revises: a91f3c07d5e2
Create Date: 2026-08-14
"""

import sqlalchemy as sa
from alembic import op

revision = "c7e4b19f8a35"
down_revision = "a91f3c07d5e2"
branch_labels = None
depends_on = None

# (cliente en Gestión, [ID_Empresa de Siges, ...])
_ALIAS: list[tuple[str, list[int]]] = [
    ("ADMIFARM", [998, 1000]),  # AG Servicios Farmaceuticos + AG Farma
    ("ARCA - JUNIN", [1373]),  # ARCA - Direccion Regional Junin
    ("ASP", [451]),  # Nutrien (confirmado por el usuario)
    ("Alvarez y Asociados", [952]),  # ARV
    ("Arag", [655]),  # Arag S.R.L.
    ("Axion Log", [630]),  # AxionLog
    ("BIND", [1343]),  # Banco Industrial (BIND es su marca)
    ("BRF (Campo Austral)", [866]),  # Campo Austral S.A.
    ("CBRE", [746]),  # CBRE Argentina
    ("CPCBA", [826]),  # CPCEPBA (Consejo Prof. Cs. Económicas PBA)
    ("Codere", [476, 455]),  # Bingos del Oeste + Bingos Platenses
    ("DEGASA", [817]),  # Desarrollos Gastronómicos S.A.
    ("Diarco | Potigian | La Gioconda", [858, 862, 863]),
    ("GIRE", [988, 1254]),  # GIRE S.A. + Gire Soluciones
    ("GRUPO RANDAZZO", [1058, 1059, 1060]),  # Empresa.ID_GrupoE=583
    ("Gob San Juan", [471]),  # Gobierno de San Juan
    ("HOSP. ITALIANO DE LA PLATA", [1065]),
    ("ILOLAY y Las taperitas", [938, 990]),
    ("ITL - EXOLGAN", [1121, 295]),  # Exolgan (nueva) + ITL
    ("Instituto Poveda", [331]),  # Instituto Pedro Poveda
    ("Laboratorios Raffo (Monte Verde)+(Asofarma)= Adium", [762, 761, 906]),
    ("Megatlón - Fiter", [829, 929]),
    ("Metropolis Financiera", [794]),  # Banco de Comercio S.A. (nombre actual)
    ("Noble Seguros", [109]),  # Noble Compañia de Seguros
    ("Resmacon", [88]),  # 'Resmacón' — desambigua el duplicado con 1147
    ("Roemmers / Maprimed", [563, 564]),
    ("Salta Refrescos", [68, 69, 585]),  # regiones Norte + Sur + Este
    ("United Logistics", [229]),  # United Logistic Company
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
