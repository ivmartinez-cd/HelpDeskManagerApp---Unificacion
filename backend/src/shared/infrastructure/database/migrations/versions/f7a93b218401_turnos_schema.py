"""turnos schema

Revision ID: f7a93b218401
Revises: e2ed69fda1ec
Create Date: 2026-08-11 14:00:00.000000

"""

import uuid
from collections.abc import Sequence
from datetime import date, time

import sqlalchemy as sa
from alembic import op

revision: str = "f7a93b218401"
down_revision: str | None = "e2ed69fda1ec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$RkJ3OWx2Z0Y2eGt2Q2ZpZ3FqZndIdw"


def upgrade() -> None:
    op.create_table(
        "turno_casilla",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_table(
        "turno_slot",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("casilla_id", sa.UUID(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=False),
        sa.Column("hora_fin", sa.Time(), nullable=False),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["casilla_id"], ["turno_casilla.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "turno_asignacion",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column(
            "vigente_desde", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False
        ),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["slot_id"], ["turno_slot.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    _seed_initial_turnos()


def _seed_initial_turnos() -> None:
    bind = op.get_bind()
    app_user_table = sa.table(
        "app_user",
        sa.column("id", sa.UUID()),
        sa.column("email", sa.String()),
        sa.column("password_hash", sa.String()),
        sa.column("full_name", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("is_superadmin", sa.Boolean()),
    )
    casilla_table = sa.table(
        "turno_casilla",
        sa.column("id", sa.UUID()),
        sa.column("nombre", sa.String()),
        sa.column("color", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    slot_table = sa.table(
        "turno_slot",
        sa.column("id", sa.UUID()),
        sa.column("casilla_id", sa.UUID()),
        sa.column("hora_inicio", sa.Time()),
        sa.column("hora_fin", sa.Time()),
        sa.column("dia_semana", sa.SmallInteger()),
        sa.column("sort_order", sa.Integer()),
    )
    asignacion_table = sa.table(
        "turno_asignacion",
        sa.column("id", sa.UUID()),
        sa.column("slot_id", sa.UUID()),
        sa.column("user_id", sa.UUID()),
        sa.column("vigente_desde", sa.Date()),
    )

    # 1. Asegurar la existencia de los operadores en app_user
    operators_data = [
        ("mjvela@canaldirecto.com.ar", "Maria Jose Vela"),
        ("ltorres@canaldirecto.com.ar", "Luna Torres"),
        ("mvillegas@canaldirecto.com.ar", "Mariano Villegas"),
        ("vipaez@canaldirecto.com.ar", "Victor Paez"),
    ]

    existing_rows = bind.execute(sa.text("SELECT id, email, full_name FROM app_user")).fetchall()
    existing_by_email = {row[1].lower(): row[0] for row in existing_rows}
    user_ids_by_name: dict[str, uuid.UUID] = {}

    for email, full_name in operators_data:
        email_lower = email.lower()
        if email_lower in existing_by_email:
            u_id = existing_by_email[email_lower]
        else:
            u_id = uuid.uuid4()
            op.bulk_insert(
                app_user_table,
                [
                    {
                        "id": u_id,
                        "email": email_lower,
                        "password_hash": _DUMMY_HASH,
                        "full_name": full_name,
                        "is_active": True,
                        "is_superadmin": False,
                    }
                ],
            )
        fn_key = full_name.split()[0].lower()
        user_ids_by_name[fn_key] = u_id

    # Add fallback matches for names
    for _u_id, _email, full_name in existing_rows:
        fn_key = full_name.split()[0].lower()
        if fn_key not in user_ids_by_name:
            user_ids_by_name[fn_key] = _u_id

    # 2. Insertar casillas
    insumos_id = uuid.uuid4()
    st_id = uuid.uuid4()

    op.bulk_insert(
        casilla_table,
        [
            {
                "id": insumos_id,
                "nombre": "INSUMOS",
                "color": "#8b5cf6",
                "sort_order": 0,
                "is_active": True,
            },
            {
                "id": st_id,
                "nombre": "ST",
                "color": "#3b82f6",
                "sort_order": 1,
                "is_active": True,
            },
        ],
    )

    slots_to_insert = []
    asignaciones_to_insert: list[dict[str, object]] = []
    today_date = date.today()

    for day in range(5):
        s1, s2, s3, s4 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        slots_to_insert.extend([
            {
                "id": s1,
                "casilla_id": insumos_id,
                "hora_inicio": time(8, 0),
                "hora_fin": time(11, 0),
                "dia_semana": day,
                "sort_order": 0,
            },
            {
                "id": s2,
                "casilla_id": insumos_id,
                "hora_inicio": time(11, 0),
                "hora_fin": time(13, 0),
                "dia_semana": day,
                "sort_order": 1,
            },
            {
                "id": s3,
                "casilla_id": insumos_id,
                "hora_inicio": time(13, 0),
                "hora_fin": time(17, 0),
                "dia_semana": day,
                "sort_order": 2,
            },
            {
                "id": s4,
                "casilla_id": insumos_id,
                "hora_inicio": time(17, 0),
                "hora_fin": time(18, 0),
                "dia_semana": day,
                "sort_order": 3,
            },
        ])

        _add_asig(asignaciones_to_insert, s1, user_ids_by_name.get("maria"), today_date)
        _add_asig(asignaciones_to_insert, s2, user_ids_by_name.get("luna"), today_date)
        _add_asig(asignaciones_to_insert, s3, user_ids_by_name.get("mariano"), today_date)
        _add_asig(asignaciones_to_insert, s4, user_ids_by_name.get("victor"), today_date)

        st1, st2, st3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
        slots_to_insert.extend([
            {
                "id": st1,
                "casilla_id": st_id,
                "hora_inicio": time(9, 0),
                "hora_fin": time(13, 0),
                "dia_semana": day,
                "sort_order": 0,
            },
            {
                "id": st2,
                "casilla_id": st_id,
                "hora_inicio": time(13, 0),
                "hora_fin": time(15, 0),
                "dia_semana": day,
                "sort_order": 1,
            },
            {
                "id": st3,
                "casilla_id": st_id,
                "hora_inicio": time(15, 0),
                "hora_fin": time(18, 0),
                "dia_semana": day,
                "sort_order": 2,
            },
        ])

        _add_asig(asignaciones_to_insert, st1, user_ids_by_name.get("victor"), today_date)
        _add_asig(asignaciones_to_insert, st2, user_ids_by_name.get("maria"), today_date)
        _add_asig(asignaciones_to_insert, st3, user_ids_by_name.get("luna"), today_date)

    op.bulk_insert(slot_table, slots_to_insert)
    if asignaciones_to_insert:
        op.bulk_insert(asignacion_table, asignaciones_to_insert)


def _add_asig(
    target_list: list[dict[str, object]],
    slot_id: uuid.UUID,
    user_id: uuid.UUID | None,
    today_date: date,
) -> None:
    if user_id:
        target_list.append({
            "id": uuid.uuid4(),
            "slot_id": slot_id,
            "user_id": user_id,
            "vigente_desde": today_date,
        })


def downgrade() -> None:
    op.drop_table("turno_asignacion")
    op.drop_table("turno_slot")
    op.drop_table("turno_casilla")
