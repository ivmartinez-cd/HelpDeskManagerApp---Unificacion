"""cleanup: eliminar SPSTs duplicados y SPSTs fake (nombre 'PST ...').

Los 35 SPSTs cuyo nombre empieza con 'PST ' representaban la base del PST mismo
(artefacto del legacy) — no son sub-prestadores reales. La FK tabla_kms.spst_id
tiene ON DELETE SET NULL, así que el DELETE los desvincula automáticamente.

Los pares duplicados de PENTACOM/MENDOZA se mergean primero (las filas de tabla_km
del 'perdedor' se reasignan al 'ganador') antes de borrar el perdedor.

Revisión: docs/liquidaciones/DEUDA_SPSTS_CREADOS_COMO_PST.md

Revision ID: c2d8f3a1b4e9
Revises: b3c9e1f5a2d7
Create Date: 2026-08-16
"""

from alembic import op

revision = "c2d8f3a1b4e9"
down_revision = "b3c9e1f5a2d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Paso 1: reasignar filas del 'perdedor' al 'ganador' en cada par duplicado ---

    # PENTACOM: Laboulaye - Roberto Gil → SPST Pentacom - Laboulaye (siges_empresa_id=138)
    op.execute("""
        UPDATE tabla_kms
        SET spst_id = '45dd0624-1700-45e9-90a7-63ff8048b47f'
        WHERE spst_id = 'c903fddd-4b08-4165-a4bf-259c44cd5132'
    """)

    # PENTACOM: PST Cordoba (sin tilde, 3 filas) → PST Córdoba (con tilde, 188 filas)
    # Ambos son fake; se mergean para no perder filas antes de que el DELETE los NULL-ee.
    op.execute("""
        UPDATE tabla_kms
        SET spst_id = '4ddcfa25-70d3-4df1-be94-4ee3af76cfe4'
        WHERE spst_id = '8a2bf0f8-080c-4422-a855-bd3387a9d96b'
    """)

    # PENTACOM: SPST Pentacom - Marcos Juarez (sin tilde, 3 filas) → Marcos Juárez (con tilde)
    op.execute("""
        UPDATE tabla_kms
        SET spst_id = 'ce0417c4-1496-4fb5-9bf6-6c1b6f345641'
        WHERE spst_id = 'ec0082a3-50d3-48e7-84a0-3dfd8d79f562'
    """)

    # PENTACOM: SPST Pentacom - Rio IV (sin tilde, 2 filas) → Río IV (con tilde)
    op.execute("""
        UPDATE tabla_kms
        SET spst_id = '1db3ad31-cf98-4e34-97fc-020cbb38d026'
        WHERE spst_id = 'df73e637-8412-4e59-ace4-6a91c7d5a96c'
    """)

    # PENTACOM: SPST Villa María (sin prefijo, 1 fila) → SPST Pentacom - Villa María
    op.execute("""
        UPDATE tabla_kms
        SET spst_id = '1b5e99c9-3d48-467f-84a5-d861fcdaed74'
        WHERE spst_id = '882b77c1-92df-499c-b740-adaefab49861'
    """)

    # --- Paso 2: eliminar duplicados 'perdedores' (filas ya reasignadas o vacías) ---
    op.execute("""
        DELETE FROM spsts WHERE id IN (
            'c903fddd-4b08-4165-a4bf-259c44cd5132',
            '8a2bf0f8-080c-4422-a855-bd3387a9d96b',
            'ec0082a3-50d3-48e7-84a0-3dfd8d79f562',
            'df73e637-8412-4e59-ace4-6a91c7d5a96c',
            '882b77c1-92df-499c-b740-adaefab49861',
            'a6b189d6-77ba-40a7-b9e4-62e8f4fb8d41',
            '92446664-e3d1-4987-9383-3598e48d36b0'
        )
    """)

    # --- Paso 3: eliminar todos los SPSTs fake con nombre 'PST ...' ---
    # ON DELETE SET NULL en tabla_kms.spst_id desvincula las 1386 filas afectadas.
    op.execute("DELETE FROM spsts WHERE nombre LIKE 'PST %'")


def downgrade() -> None:
    raise NotImplementedError(
        "Esta migración elimina datos (42 SPSTs + reasignación de tabla_kms). "
        "No es reversible automáticamente — restaurar desde backup si hace falta."
    )
