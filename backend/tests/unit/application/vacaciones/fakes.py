"""Fakes in-memory de los repositorios de vacaciones para tests de application."""

import uuid
from datetime import date

from src.modules.vacaciones.domain.entities.aprobacion import Aprobacion
from src.modules.vacaciones.domain.entities.ausencia import Ausencia, TipoAusencia
from src.modules.vacaciones.domain.entities.cargo import Cargo
from src.modules.vacaciones.domain.entities.ciclo import Ciclo
from src.modules.vacaciones.domain.entities.empleado import Empleado
from src.modules.vacaciones.domain.entities.exclusion import Exclusion
from src.modules.vacaciones.domain.entities.feriado import Feriado
from src.modules.vacaciones.domain.entities.sector import Sector
from src.modules.vacaciones.domain.entities.solicitud import (
    ESTADOS_ACTIVOS,
    EstadoSolicitud,
    Solicitud,
)
from src.modules.vacaciones.domain.errors import SigesVinculoDuplicadoError
from src.modules.vacaciones.domain.repositories.ausencia_repository import (
    FiltrosAusencias,
)
from src.modules.vacaciones.domain.repositories.empleado_repository import FiltrosEmpleados
from src.modules.vacaciones.domain.repositories.feriados_externos import FeriadoImportado
from src.modules.vacaciones.domain.repositories.notificador import (
    DecisionNotif,
    NuevaSolicitudNotif,
)
from src.modules.vacaciones.domain.repositories.sector_manager_repository import JefeSector
from src.modules.vacaciones.domain.repositories.solicitud_repository import (
    FiltrosSolicitudes,
    RangoSolapado,
)
from src.modules.vacaciones.domain.repositories.user_directory import UserInfo
from src.modules.vacaciones.domain.value_objects.config_vacaciones import ConfigVacaciones


class FakeEmpleadoRepo:
    def __init__(self, empleados: list[Empleado]) -> None:
        self._items = {e.id: e for e in empleados}

    async def get_by_id(self, empleado_id: uuid.UUID) -> Empleado | None:
        return self._items.get(empleado_id)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Empleado | None:
        return next((e for e in self._items.values() if e.user_id == user_id), None)

    async def get_by_email(self, email: str) -> Empleado | None:
        return next((e for e in self._items.values() if e.email == email), None)

    async def get_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, Empleado]:
        return {i: self._items[i] for i in ids if i in self._items}

    async def list_filtrados(self, filtros: FiltrosEmpleados) -> list[Empleado]:
        items = list(self._items.values())
        if filtros.department_id is not None:
            items = [e for e in items if e.department_id == filtros.department_id]
        if filtros.status is not None:
            items = [e for e in items if e.status is filtros.status]
        if filtros.empleado_id is not None:
            items = [e for e in items if e.id == filtros.empleado_id]
        return items

    async def count_activos_por_departamento(self, department_id: uuid.UUID) -> int:
        return sum(
            1
            for e in self._items.values()
            if e.department_id == department_id and e.esta_activo
        )

    async def add(self, empleado: Empleado) -> None:
        self._items[empleado.id] = empleado

    async def save(self, empleado: Empleado) -> None:
        self._items[empleado.id] = empleado

    async def delete(self, empleado_id: uuid.UUID) -> None:
        self._items.pop(empleado_id, None)

    async def vincular_siges(
        self, empleado_id: uuid.UUID, *, siges_empresa_id: int | None
    ) -> Empleado | None:
        empleado = self._items.get(empleado_id)
        if empleado is None:
            return None
        if siges_empresa_id is not None and any(
            e.siges_empresa_id == siges_empresa_id and e.id != empleado_id
            for e in self._items.values()
        ):
            raise SigesVinculoDuplicadoError(siges_empresa_id)
        empleado.siges_empresa_id = siges_empresa_id
        return empleado


class FakeSolicitudRepo:
    def __init__(self, solicitudes: list[Solicitud] | None = None) -> None:
        self.items: dict[uuid.UUID, Solicitud] = {s.id: s for s in (solicitudes or [])}

    def _activas(self) -> list[Solicitud]:
        return [s for s in self.items.values() if s.status in ESTADOS_ACTIVOS]

    async def get_by_id(self, solicitud_id: uuid.UUID) -> Solicitud | None:
        return self.items.get(solicitud_id)

    async def list_filtradas(self, filtros: FiltrosSolicitudes) -> list[Solicitud]:
        items = list(self.items.values())
        if filtros.status is not None:
            items = [s for s in items if s.status is filtros.status]
        if filtros.empleado_id is not None:
            items = [s for s in items if s.empleado_id == filtros.empleado_id]
        if filtros.desde is not None:
            items = [s for s in items if s.end_date >= filtros.desde]
        if filtros.hasta is not None:
            items = [s for s in items if s.start_date <= filtros.hasta]
        return items

    async def list_activas_de_empleado(
        self, empleado_id: uuid.UUID, excluir_solicitud_id: uuid.UUID | None = None
    ) -> list[Solicitud]:
        return [
            s
            for s in self._activas()
            if s.empleado_id == empleado_id and s.id != excluir_solicitud_id
        ]

    async def list_activas_de_empleados(
        self, empleado_ids: list[uuid.UUID]
    ) -> list[Solicitud]:
        return sorted(
            (s for s in self._activas() if s.empleado_id in empleado_ids),
            key=lambda s: s.start_date,
        )

    async def list_activas_solapadas_de_empleados(
        self, empleado_ids: list[uuid.UUID], rango: RangoSolapado
    ) -> list[Solicitud]:
        return [
            s
            for s in self._activas()
            if s.empleado_id in empleado_ids
            and s.id != rango.excluir_solicitud_id
            and s.solapa_con(rango.start, rango.end)
        ]

    async def list_rangos_activos_por_cargo(
        self, cargo_id: uuid.UUID, excluir_empleado_id: uuid.UUID, rango: RangoSolapado
    ) -> list[tuple[date, date]]:
        return []

    async def list_activas_solapadas_de_departamento(
        self, department_id: uuid.UUID, rango: RangoSolapado
    ) -> list[Solicitud]:
        return []

    async def list_activas_en_rango(
        self, desde: date | None, hasta: date | None, department_id: uuid.UUID | None
    ) -> list[Solicitud]:
        items = self._activas()
        if desde is not None:
            items = [s for s in items if s.end_date >= desde]
        if hasta is not None:
            items = [s for s in items if s.start_date <= hasta]
        return items

    async def add(self, solicitud: Solicitud) -> None:
        self.items[solicitud.id] = solicitud

    async def save(self, solicitud: Solicitud) -> None:
        self.items[solicitud.id] = solicitud

    async def delete(self, solicitud_id: uuid.UUID) -> None:
        self.items.pop(solicitud_id, None)


class FakeCicloRepo:
    def __init__(self, ciclos: list[Ciclo] | None = None) -> None:
        self.items: dict[uuid.UUID, Ciclo] = {c.id: c for c in (ciclos or [])}
        self.saves = 0

    async def get(self, empleado_id: uuid.UUID, year: int) -> Ciclo | None:
        return next(
            (
                c
                for c in self.items.values()
                if c.empleado_id == empleado_id and c.year == year
            ),
            None,
        )

    async def list_por_empleado(self, empleado_id: uuid.UUID) -> list[Ciclo]:
        return [c for c in self.items.values() if c.empleado_id == empleado_id]

    async def list_por_empleados(self, empleado_ids: list[uuid.UUID]) -> list[Ciclo]:
        return [c for c in self.items.values() if c.empleado_id in empleado_ids]

    async def list_por_year(self, year: int) -> list[Ciclo]:
        return [c for c in self.items.values() if c.year == year]

    async def add(self, ciclo: Ciclo) -> None:
        self.items[ciclo.id] = ciclo

    async def save(self, ciclo: Ciclo) -> None:
        self.items[ciclo.id] = ciclo
        self.saves += 1


class FakeConfigRepo:
    def __init__(self, config: ConfigVacaciones) -> None:
        self._config = config

    async def get(self) -> ConfigVacaciones:
        return self._config

    async def save(self, config: ConfigVacaciones) -> None:
        self._config = config


class FakeAusenciaRepo:
    def __init__(self, ausencias: list[Ausencia] | None = None) -> None:
        self.items: dict[uuid.UUID, Ausencia] = {a.id: a for a in (ausencias or [])}

    async def get_by_id(self, ausencia_id: uuid.UUID) -> Ausencia | None:
        return self.items.get(ausencia_id)

    async def list_filtradas(self, filtros: FiltrosAusencias) -> list[Ausencia]:
        items = list(self.items.values())
        if filtros.status is not None:
            items = [a for a in items if a.status is filtros.status]
        if filtros.tipo is not None:
            items = [a for a in items if a.tipo is filtros.tipo]
        if filtros.empleado_id is not None:
            items = [a for a in items if a.empleado_id == filtros.empleado_id]
        return items

    async def existe_activa_solapada(
        self,
        empleado_id: uuid.UUID,
        tipo: TipoAusencia,
        start: date,
        end: date,
        excluir_ausencia_id: uuid.UUID | None = None,
    ) -> bool:
        return any(
            a.empleado_id == empleado_id
            and a.tipo is tipo
            and a.status in ESTADOS_ACTIVOS
            and a.id != excluir_ausencia_id
            and a.solapa_con(start, end)
            for a in self.items.values()
        )

    async def list_aprobadas_solapadas_de_empleados(
        self, empleado_ids: list[uuid.UUID], start: date, end: date
    ) -> list[Ausencia]:
        return [
            a
            for a in self.items.values()
            if a.empleado_id in empleado_ids
            and a.status is EstadoSolicitud.APPROVED
            and a.solapa_con(start, end)
        ]

    async def add(self, ausencia: Ausencia) -> None:
        self.items[ausencia.id] = ausencia

    async def save(self, ausencia: Ausencia) -> None:
        self.items[ausencia.id] = ausencia

    async def delete(self, ausencia_id: uuid.UUID) -> None:
        self.items.pop(ausencia_id, None)


class FakeRegistradorAuditoria:
    def __init__(self) -> None:
        self.registros: list[tuple[str, str, str | None, dict[str, object]]] = []

    async def registrar(
        self,
        accion: str,
        entidad: str,
        entidad_id: str | None,
        metadata: dict[str, object],
    ) -> None:
        self.registros.append((accion, entidad, entidad_id, metadata))


class FakeFeriadoRepo:
    def __init__(self, feriados: list[Feriado] | None = None) -> None:
        self.items = feriados or []

    async def list_all(self) -> list[Feriado]:
        return self.items

    async def existe_no_deduce_en(self, fecha: date) -> bool:
        return any(f.date == fecha and not f.deducts_vacation for f in self.items)

    async def get_by_id(self, feriado_id: uuid.UUID) -> Feriado | None:
        return next((f for f in self.items if f.id == feriado_id), None)

    async def get_by_date(self, fecha: date) -> Feriado | None:
        return next((f for f in self.items if f.date == fecha), None)

    async def add(self, feriado: Feriado) -> None:
        self.items.append(feriado)

    async def save(self, feriado: Feriado) -> None:
        self.items = [feriado if f.id == feriado.id else f for f in self.items]

    async def delete(self, feriado_id: uuid.UUID) -> None:
        self.items = [f for f in self.items if f.id != feriado_id]

    async def upsert_por_fecha(self, feriado: Feriado) -> None:
        existente = await self.get_by_date(feriado.date)
        if existente is None:
            self.items.append(feriado)
        else:
            existente.name = feriado.name


class FakeExclusionRepo:
    def __init__(self, exclusiones: list[Exclusion] | None = None) -> None:
        self.items = exclusiones or []

    async def list_all(self) -> list[Exclusion]:
        return self.items

    async def list_por_empleado(self, empleado_id: uuid.UUID) -> list[Exclusion]:
        return [e for e in self.items if e.contraparte_de(empleado_id) is not None]

    async def get_by_id(self, exclusion_id: uuid.UUID) -> Exclusion | None:
        return next((e for e in self.items if e.id == exclusion_id), None)

    async def add(self, exclusion: Exclusion) -> None:
        self.items.append(exclusion)

    async def delete(self, exclusion_id: uuid.UUID) -> None:
        self.items = [e for e in self.items if e.id != exclusion_id]


class FakeCargoRepo:
    def __init__(self, cargos: list[Cargo]) -> None:
        self._items = {c.id: c for c in cargos}
        self.empleados_por_cargo: dict[uuid.UUID, int] = {}

    async def get_by_id(self, cargo_id: uuid.UUID) -> Cargo | None:
        return self._items.get(cargo_id)

    async def get_by_name(self, name: str) -> Cargo | None:
        return next((c for c in self._items.values() if c.name == name), None)

    async def list_all(self) -> list[Cargo]:
        return list(self._items.values())

    async def count_empleados(self, cargo_id: uuid.UUID) -> int:
        return self.empleados_por_cargo.get(cargo_id, 0)

    async def add(self, cargo: Cargo) -> None:
        self._items[cargo.id] = cargo

    async def save(self, cargo: Cargo) -> None:
        self._items[cargo.id] = cargo

    async def delete(self, cargo_id: uuid.UUID) -> None:
        self._items.pop(cargo_id, None)


class FakeSectorRepo:
    def __init__(self, sectores: list[Sector]) -> None:
        self._items = {s.id: s for s in sectores}

    async def list_all(self) -> list[Sector]:
        return list(self._items.values())

    async def get_by_id(self, sector_id: uuid.UUID) -> Sector | None:
        return self._items.get(sector_id)

    async def get_by_name(self, name: str) -> Sector | None:
        return next((s for s in self._items.values() if s.name == name), None)

    async def add(self, sector: Sector) -> None:
        self._items[sector.id] = sector

    async def save(self, sector: Sector) -> None:
        self._items[sector.id] = sector

    async def delete(self, sector_id: uuid.UUID) -> None:
        self._items.pop(sector_id, None)


class FakeAprobacionRepo:
    def __init__(self) -> None:
        self.items: list[Aprobacion] = []

    async def add(self, aprobacion: Aprobacion) -> None:
        self.items.append(aprobacion)

    async def list_por_solicitud(self, solicitud_id: uuid.UUID) -> list[Aprobacion]:
        return [a for a in self.items if a.solicitud_id == solicitud_id]

    async def list_por_solicitudes(
        self, solicitud_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[Aprobacion]]:
        return {
            sid: [a for a in self.items if a.solicitud_id == sid] for sid in solicitud_ids
        }


class FakeNotificador:
    def __init__(self) -> None:
        self.nuevas: list[NuevaSolicitudNotif] = []
        self.decisiones: list[DecisionNotif] = []

    async def notificar_nueva_solicitud(self, notif: NuevaSolicitudNotif) -> None:
        self.nuevas.append(notif)

    async def notificar_decision(self, notif: DecisionNotif) -> None:
        self.decisiones.append(notif)


class FakeImpactoTurnosLookup:
    """`users_con_turnos` = usuarios que tienen franjas en cualquier rango."""

    def __init__(self, users_con_turnos: set[uuid.UUID] | None = None) -> None:
        self.users_con_turnos = users_con_turnos or set()
        self.consultas: list[tuple[uuid.UUID, date, date]] = []

    async def tiene_turnos_en(self, user_id: uuid.UUID, desde: date, hasta: date) -> bool:
        self.consultas.append((user_id, desde, hasta))
        return user_id in self.users_con_turnos


class FixedClock:
    def __init__(self, fecha: date) -> None:
        self._fecha = fecha

    def hoy(self) -> date:
        return self._fecha


class FakeSectorManagerRepo:
    def __init__(self, jefes: list[JefeSector] | None = None) -> None:
        self.items: list[JefeSector] = jefes or []

    async def get_sector_de_usuario(self, user_id: uuid.UUID) -> uuid.UUID | None:
        return next((j.department_id for j in self.items if j.user_id == user_id), None)

    async def list_jefes(self) -> list[JefeSector]:
        return list(self.items)

    async def asignar(self, user_id: uuid.UUID, department_id: uuid.UUID) -> None:
        await self.desasignar(user_id)
        self.items.append(JefeSector(user_id=user_id, department_id=department_id))

    async def desasignar(self, user_id: uuid.UUID) -> None:
        self.items = [j for j in self.items if j.user_id != user_id]


class FakeUserDirectory:
    def __init__(self, users: list[UserInfo] | None = None) -> None:
        self._items = {u.id: u for u in (users or [])}

    async def list_activos(self) -> list[UserInfo]:
        return list(self._items.values())

    async def get_by_id(self, user_id: uuid.UUID) -> UserInfo | None:
        return self._items.get(user_id)

    async def get_by_ids(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserInfo]:
        return {i: self._items[i] for i in user_ids if i in self._items}


class FakeFeriadosExternosProvider:
    def __init__(self, feriados: list[FeriadoImportado] | None = None) -> None:
        self.feriados = feriados or []

    async def fetch(self, year: int) -> list[FeriadoImportado]:
        return self.feriados
