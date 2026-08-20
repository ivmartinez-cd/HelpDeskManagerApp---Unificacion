"""ABM de grillas variantes (modo vacaciones, ADR-025) con repos fake."""

import uuid
from datetime import date, time

import pytest

from src.modules.turnos.application.dtos.grilla_variante_dtos import (
    CreateGrillaVarianteCommand,
    UpdateGrillaVarianteCommand,
    VarianteSlotInput,
)
from src.modules.turnos.application.use_cases.cancel_grilla_variante import (
    CancelGrillaVariante,
)
from src.modules.turnos.application.use_cases.create_grilla_variante import (
    CreateGrillaVariante,
)
from src.modules.turnos.application.use_cases.grilla_variante_support import (
    GrillaVarianteDependencies,
)
from src.modules.turnos.application.use_cases.list_grilla_variantes import (
    ListGrillaVariantes,
)
from src.modules.turnos.application.use_cases.precargar_grilla_variante import (
    PrecargarGrillaVariante,
    PrecargarGrillaVarianteDependencies,
)
from src.modules.turnos.application.use_cases.update_grilla_variante import (
    UpdateGrillaVariante,
)
from src.modules.turnos.domain.errors import (
    GrillaVarianteNotFoundError,
    OverlappingVarianteError,
    VarianteCasillaInvalidaError,
    VarianteNoEditableError,
    VarianteOperadorSolapadoError,
)
from src.modules.turnos.domain.repositories.ausencias_lookup import AusenciaAprobada
from src.modules.turnos.domain.repositories.user_provider import UserInfo
from tests.unit.domain.turnos.caso_majo import VIGENCIA_DESDE, VIGENCIA_HASTA, CasoMajo
from tests.unit.domain.turnos.fakes import (
    FakeAsignacionRepository,
    FakeAusenciasLookup,
    FakeCasillaRepository,
    FakeGrillaVarianteRepository,
    FakeSlotRepository,
    FakeUserProvider,
)


class _Escenario:
    def __init__(self) -> None:
        self.caso = CasoMajo()
        self.casillas = FakeCasillaRepository()
        for c in self.caso.casillas:
            self.casillas.rows[c.id] = c
        self.slots = FakeSlotRepository()
        for s in self.caso.slots:
            self.slots.rows[s.id] = s
        self.asignaciones = FakeAsignacionRepository()
        for a in self.caso.asignaciones:
            self.asignaciones.rows[a.id] = a
        self.users = FakeUserProvider()
        for uid, nombre in self.caso.nombres.items():
            self.users.users[uid] = UserInfo(id=uid, full_name=nombre)
        self.variantes = FakeGrillaVarianteRepository()
        self.ausencias = FakeAusenciasLookup()
        self.deps = GrillaVarianteDependencies(
            variantes=self.variantes,
            casillas=self.casillas,
            slots=self.slots,
            users=self.users,
            ausencias=self.ausencias,
        )

    def franja(
        self, casilla_id: uuid.UUID, inicio: time, fin: time, *users: uuid.UUID, dia: int = 0
    ) -> VarianteSlotInput:
        return VarianteSlotInput(
            casilla_id=casilla_id,
            dia_semana=dia,
            hora_inicio=inicio,
            hora_fin=fin,
            user_ids=list(users),
        )

    def command(self, slots: list[VarianteSlotInput] | None = None) -> CreateGrillaVarianteCommand:
        c = self.caso
        return CreateGrillaVarianteCommand(
            motivo="Vacaciones M. J. Vela",
            origen_texto=None,
            desde=VIGENCIA_DESDE,
            hasta=VIGENCIA_HASTA,
            slots=slots
            if slots is not None
            else [
                self.franja(c.insumos.id, time(8, 30), time(11), c.mariano),
                self.franja(c.st.id, time(8), time(9), c.mariana),
            ],
            created_by_user_id=uuid.uuid4(),
        )


async def test_crear_persiste_y_devuelve_advertencias_de_hueco_con_nombres() -> None:
    esc = _Escenario()

    dto = await CreateGrillaVariante(esc.deps).execute(esc.command())

    assert dto.id in esc.variantes.rows
    assert dto.estado == "ACTIVA"
    assert [s.casilla_nombre for s in dto.slots] == ["INSUMOS", "ST"]
    assert dto.slots[0].operadores[0].user_name == "Mariano Gomez"
    huecos_insumos_lunes = [
        (a.hora_inicio, a.hora_fin)
        for a in dto.advertencias
        if a.tipo == "HUECO" and a.casilla_nombre == "INSUMOS" and a.dia_semana == 0
    ]
    assert huecos_insumos_lunes == [(time(8), time(8, 30)), (time(11), time(18))]


async def test_crear_rechaza_solape_de_vigencia_con_otra_activa() -> None:
    esc = _Escenario()
    await CreateGrillaVariante(esc.deps).execute(esc.command())
    otra = CreateGrillaVarianteCommand(
        motivo=None,
        origen_texto=None,
        desde=date(2026, 8, 28),
        hasta=date(2026, 9, 4),
        slots=esc.command().slots,
        created_by_user_id=uuid.uuid4(),
    )
    with pytest.raises(OverlappingVarianteError):
        await CreateGrillaVariante(esc.deps).execute(otra)


async def test_crear_rechaza_casilla_inexistente_y_operador_duplicado_en_solape() -> None:
    esc = _Escenario()
    c = esc.caso
    with pytest.raises(VarianteCasillaInvalidaError):
        await CreateGrillaVariante(esc.deps).execute(
            esc.command([esc.franja(uuid.uuid4(), time(8), time(9), c.luna)])
        )
    with pytest.raises(VarianteOperadorSolapadoError):
        await CreateGrillaVariante(esc.deps).execute(
            esc.command(
                [
                    esc.franja(c.insumos.id, time(11), time(13), c.luna),
                    esc.franja(c.st.id, time(12), time(14), c.luna),
                ]
            )
        )


async def test_crear_advierte_cubriente_con_vacaciones_aprobadas_solapadas() -> None:
    esc = _Escenario()
    esc.ausencias.rows.append(
        AusenciaAprobada(user_id=esc.caso.mariana, desde=date(2026, 8, 27), hasta=date(2026, 9, 1))
    )

    dto = await CreateGrillaVariante(esc.deps).execute(esc.command())

    ausente = next(a for a in dto.advertencias if a.tipo == "OPERADOR_AUSENTE")
    assert (ausente.user_name, ausente.desde) == ("Mariana Rodriguez", date(2026, 8, 27))


async def test_editar_reemplaza_in_place_y_no_conflictua_consigo_misma() -> None:
    esc = _Escenario()
    creada = await CreateGrillaVariante(esc.deps).execute(esc.command())

    editada = await UpdateGrillaVariante(esc.deps).execute(
        UpdateGrillaVarianteCommand(
            variante_id=creada.id,
            motivo="Vacaciones (extendidas)",
            origen_texto=None,
            desde=VIGENCIA_DESDE,
            hasta=date(2026, 8, 31),
            slots=[esc.franja(esc.caso.st.id, time(8), time(9), esc.caso.mariana)],
        )
    )

    assert editada.id == creada.id
    assert editada.hasta == date(2026, 8, 31)
    assert len(editada.slots) == 1
    assert editada.created_by_user_id == creada.created_by_user_id
    assert len(esc.variantes.rows) == 1


async def test_editar_una_cancelada_o_inexistente_falla() -> None:
    esc = _Escenario()
    creada = await CreateGrillaVariante(esc.deps).execute(esc.command())
    await CancelGrillaVariante(esc.deps).execute(creada.id)
    assert esc.variantes.rows[creada.id].estado == "CANCELADA"

    comando = UpdateGrillaVarianteCommand(
        variante_id=creada.id,
        motivo=None,
        origen_texto=None,
        desde=VIGENCIA_DESDE,
        hasta=VIGENCIA_HASTA,
        slots=esc.command().slots,
    )
    with pytest.raises(VarianteNoEditableError):
        await UpdateGrillaVariante(esc.deps).execute(comando)
    with pytest.raises(GrillaVarianteNotFoundError):
        await CancelGrillaVariante(esc.deps).execute(uuid.uuid4())


async def test_listar_ordena_por_desde_desc_y_filtra_vigentes() -> None:
    esc = _Escenario()
    await CreateGrillaVariante(esc.deps).execute(esc.command())
    vieja = await CreateGrillaVariante(esc.deps).execute(
        CreateGrillaVarianteCommand(
            motivo="pasada",
            origen_texto=None,
            desde=date(2026, 7, 6),
            hasta=date(2026, 7, 10),
            slots=esc.command().slots,
            created_by_user_id=uuid.uuid4(),
        )
    )

    todas = await ListGrillaVariantes(esc.deps).execute(hoy=date(2026, 8, 20))
    vigentes = await ListGrillaVariantes(esc.deps).execute(
        solo_vigentes=True, hoy=date(2026, 8, 20)
    )

    assert [v.motivo for v in todas] == ["Vacaciones M. J. Vela", "pasada"]
    assert [v.id for v in vigentes] != [vieja.id] and len(vigentes) == 1
    assert any(a.tipo == "HUECO" for a in todas[0].advertencias)


async def test_precarga_devuelve_titular_sin_el_ausente_y_marca_sus_franjas() -> None:
    esc = _Escenario()
    c = esc.caso
    esc.ausencias.rows.append(
        AusenciaAprobada(user_id=c.luna, desde=date(2026, 8, 26), hasta=date(2026, 8, 26))
    )
    deps = PrecargarGrillaVarianteDependencies(base=esc.deps, asignaciones=esc.asignaciones)

    dto = await PrecargarGrillaVariante(deps).execute(
        ausente_user_id=c.majo, desde=VIGENCIA_DESDE, hasta=VIGENCIA_HASTA
    )

    assert dto.ausente_nombre == "Maria Jose Vela"
    assert len(dto.slots) == 35  # 7 franjas x 5 días
    lunes = [s for s in dto.slots if s.dia_semana == 0]
    de_majo = [s for s in lunes if s.requiere_cobertura]
    assert [(s.casilla_nombre, s.hora_inicio) for s in de_majo] == [
        ("INSUMOS", time(8)),
        ("ST", time(13)),
    ]
    assert all(s.operadores == [] for s in de_majo)
    assert all(
        c.majo not in [o.user_id for o in s.operadores] for s in dto.slots
    )
    assert [a.user_name for a in dto.advertencias] == ["Luna Torres"]
