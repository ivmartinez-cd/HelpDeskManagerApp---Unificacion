"""Caso real de aceptación del modo vacaciones (ADR-025): vacaciones de
M. J. Vela del 24 al 28/08/2026, con refuerzo puntual de Mariana en ST 8-9.
Ver docs/coberturas/PLAN_COBERTURA_VACACIONES_MAJO_2026-08-24.md."""

import uuid
from dataclasses import dataclass, field
from datetime import date, time

from src.modules.turnos.domain.entities.asignacion import Asignacion
from src.modules.turnos.domain.entities.casilla import Casilla
from src.modules.turnos.domain.entities.grilla_variante import GrillaVariante, VarianteSlot
from src.modules.turnos.domain.entities.slot import Slot

DIAS_LABORABLES = range(5)  # lunes a viernes
VIGENCIA_DESDE = date(2026, 8, 24)
VIGENCIA_HASTA = date(2026, 8, 28)
MIERCOLES_DENTRO = date(2026, 8, 26)
MIERCOLES_SIGUIENTE = date(2026, 9, 2)
LUNES_VUELTA = date(2026, 8, 31)


@dataclass
class CasoMajo:
    majo: uuid.UUID = field(default_factory=uuid.uuid4)
    luna: uuid.UUID = field(default_factory=uuid.uuid4)
    mariano: uuid.UUID = field(default_factory=uuid.uuid4)
    victor: uuid.UUID = field(default_factory=uuid.uuid4)
    mariana: uuid.UUID = field(default_factory=uuid.uuid4)
    insumos: Casilla = field(
        default_factory=lambda: Casilla(
            id=uuid.uuid4(), nombre="INSUMOS", color="#F7941D", sort_order=0, is_active=True
        )
    )
    st: Casilla = field(
        default_factory=lambda: Casilla(
            id=uuid.uuid4(), nombre="ST", color="#58595B", sort_order=1, is_active=True
        )
    )
    slots: list[Slot] = field(default_factory=list)
    asignaciones: list[Asignacion] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.slots:
            self._armar_titular()

    @property
    def casillas(self) -> list[Casilla]:
        return [self.insumos, self.st]

    @property
    def nombres(self) -> dict[uuid.UUID, str]:
        return {
            self.majo: "Maria Jose Vela",
            self.luna: "Luna Torres",
            self.mariano: "Mariano Gomez",
            self.victor: "Victor Paez",
            self.mariana: "Mariana Rodriguez",
        }

    def _armar_titular(self) -> None:
        """INSUMOS: 8-11 Majo · 11-13 Luna · 13-17 Mariano · 17-18 Victor
        ST:      9-13 Victor · 13-15 Majo · 15-18 Luna  (L-V, igual todos los días)."""
        plan = [
            (self.insumos, 8, 11, self.majo),
            (self.insumos, 11, 13, self.luna),
            (self.insumos, 13, 17, self.mariano),
            (self.insumos, 17, 18, self.victor),
            (self.st, 9, 13, self.victor),
            (self.st, 13, 15, self.majo),
            (self.st, 15, 18, self.luna),
        ]
        for dia in DIAS_LABORABLES:
            for orden, (casilla, inicio, fin, user) in enumerate(plan):
                self._agregar_titular(casilla, dia, time(inicio), time(fin), orden, user)

    def _agregar_titular(
        self, casilla: Casilla, dia: int, inicio: time, fin: time, orden: int, user: uuid.UUID
    ) -> None:
        slot = Slot(
            id=uuid.uuid4(),
            casilla_id=casilla.id,
            hora_inicio=inicio,
            hora_fin=fin,
            dia_semana=dia,
            sort_order=orden,
        )
        self.slots.append(slot)
        self.asignaciones.append(
            Asignacion(
                id=uuid.uuid4(),
                slot_id=slot.id,
                user_id=user,
                vigente_desde=date(2026, 1, 1),
                vigente_hasta=None,
            )
        )

    def variante_esperada(self, *, created_by: uuid.UUID | None = None) -> GrillaVariante:
        """INSUMOS: 8:30-11 Mariano · 11-13 Luna · 13-17 Mariano · 17-18 Victor
        ST:      8-9 Mariana · 9-14 Victor · 14-18 Luna."""
        plan = [
            (self.insumos, time(8, 30), time(11), self.mariano),
            (self.insumos, time(11), time(13), self.luna),
            (self.insumos, time(13), time(17), self.mariano),
            (self.insumos, time(17), time(18), self.victor),
            (self.st, time(8), time(9), self.mariana),
            (self.st, time(9), time(14), self.victor),
            (self.st, time(14), time(18), self.luna),
        ]
        slots = [
            VarianteSlot(
                id=uuid.uuid4(),
                casilla_id=casilla.id,
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
                sort_order=orden,
                user_ids=[user],
            )
            for dia in DIAS_LABORABLES
            for orden, (casilla, inicio, fin, user) in enumerate(plan)
        ]
        return GrillaVariante(
            id=uuid.uuid4(),
            motivo="Vacaciones M. J. Vela",
            origen_texto="Solicitud de vacaciones M. J. Vela 24-28/08",
            desde=VIGENCIA_DESDE,
            hasta=VIGENCIA_HASTA,
            estado="ACTIVA",
            created_by_user_id=created_by or uuid.uuid4(),
            slots=slots,
        )
