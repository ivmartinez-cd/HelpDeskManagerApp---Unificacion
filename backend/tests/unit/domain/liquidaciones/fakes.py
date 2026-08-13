"""Fakes en memoria de los puertos de liquidaciones — para tests de casos de uso.
Simplificación consciente: `list_by_prestador` de Incidente/Liquidacion no filtra de
verdad por prestador (devuelve todo lo cargado) — alcanza para tests de un solo
prestador, que es el caso de uso real de estos fakes hoy."""

import dataclasses
import uuid
from collections.abc import Sequence
from datetime import date, datetime
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.entities.observacion import Observacion
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.regla_alerta import ReglaAlerta
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
    ResultadoImportacion,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    AlertaGenerada,
    IncidenteEvaluado,
    ObservacionGenerada,
)


class FakePrestadorRepository:
    def __init__(self, rows: dict[UUID, Prestador] | None = None) -> None:
        self.rows = rows or {}

    async def get_by_id(self, prestador_id: UUID) -> Prestador | None:
        return self.rows.get(prestador_id)

    async def get_by_nombre_corto(self, nombre_corto: str) -> Prestador | None:
        return next((p for p in self.rows.values() if p.nombre_corto == nombre_corto), None)

    async def list_con_cd_id(self) -> list[Prestador]:
        return [p for p in self.rows.values() if p.cd_prestador_id is not None]

    async def get_by_cd_id(self, cd_id: int) -> Prestador | None:
        return next((p for p in self.rows.values() if p.cd_prestador_id == cd_id), None)

    async def list_all(self, *, solo_activos: bool = False) -> list[Prestador]:
        rows = self.rows.values()
        return [p for p in rows if not solo_activos or p.activo]

    async def create(
        self, *, nombre: str, nombre_corto: str, cuit: str | None, region: str | None
    ) -> Prestador:
        row = Prestador(
            id=uuid.uuid4(),
            nombre=nombre,
            nombre_corto=nombre_corto,
            cuit=cuit,
            region=region,
            activo=True,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        self.rows[row.id] = row
        return row


class FakeLiquidacionRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, Liquidacion] = {}

    async def get_by_id(self, liquidacion_id: UUID) -> Liquidacion | None:
        return self.rows.get(liquidacion_id)

    async def list_filtered(
        self,
        prestador_id: UUID | None = None,
        estado: str | None = None,
        periodo: str | None = None,
    ) -> list[Liquidacion]:
        rows: list[Liquidacion] = list(self.rows.values())
        if prestador_id is not None:
            rows = [r for r in rows if r.prestador_id == prestador_id]
        if estado is not None:
            rows = [r for r in rows if r.estado == estado]
        if periodo is not None:
            rows = [r for r in rows if r.periodo == periodo]
        return rows

    async def list_numeros_liquidacion(self) -> set[str]:
        return {r.numero_liquidacion for r in self.rows.values() if r.numero_liquidacion}

    async def list_periodos(self) -> list[str]:
        return sorted({r.periodo for r in self.rows.values()}, reverse=True)

    async def create(
        self,
        *,
        prestador_id: UUID,
        numero_liquidacion: str | None,
        periodo: str,
        tipo_liquidacion: str,
        nombre_archivo: str | None,
        total_incidentes: int,
        total_importe: float,
    ) -> Liquidacion:
        row = Liquidacion(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            numero_liquidacion=numero_liquidacion,
            periodo=periodo,
            tipo_liquidacion=tipo_liquidacion,
            nombre_archivo=nombre_archivo,
            fecha_importacion=datetime(2026, 1, 1),
            estado="abierta",
            total_incidentes=total_incidentes,
            total_alertas=0,
            total_importe=total_importe,
        )
        self.rows[row.id] = row
        return row

    async def update_estado(self, liquidacion_id: UUID, estado: str) -> None:
        self.rows[liquidacion_id] = dataclasses.replace(self.rows[liquidacion_id], estado=estado)

    async def update_extra(
        self,
        liquidacion_id: UUID,
        concepto_extra: str | None,
        monto_extra: float | None,
    ) -> Liquidacion | None:
        row = self.rows.get(liquidacion_id)
        if row is None:
            return None
        updated = dataclasses.replace(row, concepto_extra=concepto_extra, monto_extra=monto_extra)
        self.rows[liquidacion_id] = updated
        return updated

    async def update_total_alertas(self, liquidacion_id: UUID, total_alertas: int) -> None:
        self.rows[liquidacion_id] = dataclasses.replace(
            self.rows[liquidacion_id], total_alertas=total_alertas
        )

    async def delete(self, liquidacion_id: UUID) -> None:
        self.rows.pop(liquidacion_id, None)


class FakeIncidenteRepository:
    def __init__(self) -> None:
        self.rows: dict[UUID, Incidente] = {}
        self.evaluaciones_aplicadas: list[IncidenteEvaluado] = []

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Incidente]:
        return [i for i in self.rows.values() if i.liquidacion_id == liquidacion_id]

    async def list_by_prestador(self, prestador_id: UUID) -> list[Incidente]:
        return list(self.rows.values())

    async def bulk_create(
        self, liquidacion_id: UUID, incidentes: Sequence[IncidenteImportado]
    ) -> list[Incidente]:
        creados = [
            Incidente(
                id=uuid.uuid4(),
                liquidacion_id=liquidacion_id,
                numero_incidente=i.numero_incidente,
                rubro=i.rubro,
                tipo=i.tipo,
                empresa_nombre=i.empresa_nombre,
                sucursal_nombre=i.sucursal_nombre,
                nro_serie=i.nro_serie,
                fecha_cierre=i.fecha_cierre,
                costo_servicio_cobrado=i.costo_servicio_cobrado,
                cant_km_cobrado=i.cant_km_cobrado,
                costo_km_cobrado=i.costo_km_cobrado,
                total_viaje_cobrado=i.total_viaje_cobrado,
                costo_total_cobrado=i.costo_total_cobrado,
                pasa_it=i.pasa_it,
                costo_servicio_esperado=None,
                cant_km_esperado=None,
                costo_km_esperado=None,
                estado_validacion="pendiente",
            )
            for i in incidentes
        ]
        for row in creados:
            self.rows[row.id] = row
        return creados

    async def apply_evaluacion(self, resultados: Sequence[IncidenteEvaluado]) -> None:
        self.evaluaciones_aplicadas.extend(resultados)
        for r in resultados:
            row = self.rows.get(r.incidente_id)
            if row is None:
                continue
            self.rows[r.incidente_id] = dataclasses.replace(
                row,
                costo_servicio_esperado=r.costo_servicio_esperado,
                cant_km_esperado=r.cant_km_esperado,
                costo_km_esperado=r.costo_km_esperado,
                estado_validacion=r.estado_validacion,
            )


class FakeAlertaRepository:
    def __init__(self) -> None:
        self.por_liquidacion: dict[UUID, list[Alerta]] = {}

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Alerta]:
        return self.por_liquidacion.get(liquidacion_id, [])

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, alertas: Sequence[AlertaGenerada]
    ) -> list[Alerta]:
        creadas = [
            Alerta(
                id=uuid.uuid4(),
                incidente_id=a.incidente_id,
                liquidacion_id=liquidacion_id,
                tipo_alerta=a.tipo_alerta,
                descripcion=a.descripcion,
                datos_contexto=a.datos_contexto,
                riesgo=a.riesgo,
                estado="pendiente",
                fecha_generacion=datetime(2026, 1, 1),
            )
            for a in alertas
        ]
        self.por_liquidacion[liquidacion_id] = creadas
        return creadas


class FakeObservacionRepository:
    def __init__(self) -> None:
        self.por_liquidacion: dict[UUID, list[Observacion]] = {}

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Observacion]:
        return self.por_liquidacion.get(liquidacion_id, [])

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, observaciones: Sequence[ObservacionGenerada]
    ) -> list[Observacion]:
        creadas = [
            Observacion(
                id=uuid.uuid4(),
                liquidacion_id=liquidacion_id,
                tipo_observacion=o.tipo_observacion,
                severidad=o.severidad,
                titulo=o.titulo,
                descripcion=o.descripcion,
                datos_contexto=o.datos_contexto,
                monto_cobrado=o.monto_cobrado,
                monto_esperado=o.monto_esperado,
                diferencia=round(o.monto_cobrado - o.monto_esperado, 2),
                estado="pendiente",
                regla_codigo=o.regla_codigo,
                fecha_generacion=datetime(2026, 1, 1),
            )
            for o in observaciones
        ]
        self.por_liquidacion[liquidacion_id] = creadas
        return creadas


class FakeReglaAlertaRepository:
    def __init__(self, activas: dict[str, ReglaAlerta] | None = None) -> None:
        self.activas = activas or {}

    async def list_activas(self) -> dict[str, ReglaAlerta]:
        return self.activas

    async def list_all(self) -> list[ReglaAlerta]:
        return list(self.activas.values())


class FakeSpstRepository:
    def __init__(self, rows: list[Spst] | None = None) -> None:
        self.rows = rows or []

    async def get_by_id(self, spst_id: UUID) -> Spst | None:
        return next((s for s in self.rows if s.id == spst_id), None)

    async def list_by_prestador(self, prestador_id: UUID) -> list[Spst]:
        return [s for s in self.rows if s.prestador_id == prestador_id]

    async def create(
        self,
        *,
        prestador_id: UUID,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona: str | None,
    ) -> Spst:
        row = Spst(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            nombre=nombre,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            zona=zona,
            activo=True,
            created_at=datetime(2026, 1, 1),
        )
        self.rows.append(row)
        return row


class FakeTablaKmRepository:
    def __init__(self, rows: list[TablaKm] | None = None) -> None:
        self.rows = rows or []

    async def list_by_prestador(self, prestador_id: UUID) -> list[TablaKm]:
        return [t for t in self.rows if t.prestador_id == prestador_id]

    async def create(
        self,
        *,
        prestador_id: UUID,
        spst_id: UUID | None,
        empresa_nombre: str,
        sucursal_nombre: str,
        observaciones: str | None,
        domicilio_cliente: str | None,
        localidad_cliente: str | None,
        provincia_cliente: str | None,
        kms_recorrido: float,
        umbral_viatico: float,
        aplica_viatico: bool,
        kms_a_facturar: float,
        url_maps: str | None,
    ) -> TablaKm:
        row = TablaKm(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            spst_id=spst_id,
            empresa_nombre=empresa_nombre,
            sucursal_nombre=sucursal_nombre,
            observaciones=observaciones,
            domicilio_cliente=domicilio_cliente,
            localidad_cliente=localidad_cliente,
            provincia_cliente=provincia_cliente,
            kms_recorrido=kms_recorrido,
            umbral_viatico=umbral_viatico,
            aplica_viatico=aplica_viatico,
            kms_a_facturar=kms_a_facturar,
            url_maps=url_maps,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        self.rows.append(row)
        return row


class FakeTarifarioRepository:
    def __init__(self, rows: list[Tarifario] | None = None) -> None:
        self.rows = rows or []

    async def list_by_prestador(self, prestador_id: UUID) -> list[Tarifario]:
        return [t for t in self.rows if t.prestador_id == prestador_id]

    async def create(
        self,
        *,
        prestador_id: UUID,
        tipo_servicio: str,
        zona: str | None,
        costo_servicio: float,
        costo_km: float,
        vigencia_desde: date,
        vigencia_hasta: date | None,
    ) -> Tarifario:
        row = Tarifario(
            id=uuid.uuid4(),
            prestador_id=prestador_id,
            tipo_servicio=tipo_servicio,
            zona=zona,
            costo_servicio=costo_servicio,
            costo_km=costo_km,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=vigencia_hasta,
            created_at=datetime(2026, 1, 1),
        )
        self.rows.append(row)
        return row


class FakeLiquidacionFileParser:
    """Devuelve un `ResultadoImportacion` fijo sin pasar por pandas/lxml."""

    def __init__(self, resultado: ResultadoImportacion) -> None:
        self.resultado = resultado
        self.calls: list[tuple[bytes, str]] = []

    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacion:
        self.calls.append((contenido, nombre_archivo))
        return self.resultado
