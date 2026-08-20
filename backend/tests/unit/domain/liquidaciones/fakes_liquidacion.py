"""Fakes en memoria del agregado Liquidación (liquidación/incidentes/alertas/
observaciones) — separado de `fakes.py` (§4) porque son los cuatro fakes que
crecen juntos en los tests de sync y reconciliación contra AyC. Simplificaciones
conscientes: `list_by_prestador` de Incidente no filtra por prestador de verdad,
y `delete_by_ids` no simula `ON DELETE CASCADE` (esa cascada se valida contra
Postgres en `tests/integration`)."""

import dataclasses
import uuid
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from src.modules.liquidaciones.domain.entities.alerta import Alerta
from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.entities.observacion import Observacion
from src.modules.liquidaciones.domain.services.conciliar_alertas import AlertaConciliada
from src.modules.liquidaciones.domain.value_objects.incidente_actualizado import (
    IncidenteActualizado,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    IncidenteImportado,
)
from src.modules.liquidaciones.domain.value_objects.motor_reglas_resultado import (
    IncidenteEvaluado,
    ObservacionGenerada,
)


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

    async def update_estado(self, liquidacion_id: UUID, estado: str) -> Liquidacion | None:
        row = self.rows.get(liquidacion_id)
        if row is None:
            return None
        updated = dataclasses.replace(row, estado=estado)
        self.rows[liquidacion_id] = updated
        return updated

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

    async def update_totales(
        self, liquidacion_id: UUID, total_incidentes: int, total_importe: float
    ) -> None:
        self.rows[liquidacion_id] = dataclasses.replace(
            self.rows[liquidacion_id],
            total_incidentes=total_incidentes,
            total_importe=total_importe,
        )

    async def list_activas_por_prestador_con_numero(
        self, prestador_id: UUID, estados: frozenset[str]
    ) -> list[Liquidacion]:
        return [
            r for r in self.rows.values()
            if r.prestador_id == prestador_id
            and r.numero_liquidacion is not None
            and r.estado in estados
        ]

    async def delete(self, liquidacion_id: UUID) -> bool:
        if liquidacion_id not in self.rows:
            return False
        self.rows.pop(liquidacion_id)
        return True


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

    async def empresas_con_actividad_reciente(
        self, prestador_id: UUID, desde_periodo: str
    ) -> set[str]:
        return {i.empresa_nombre for i in self.rows.values() if i.empresa_nombre is not None}

    async def update_cobrados(self, cambios: Sequence[IncidenteActualizado]) -> None:
        for c in cambios:
            row = self.rows.get(c.incidente_id)
            if row is None:
                continue
            self.rows[c.incidente_id] = dataclasses.replace(
                row,
                rubro=c.rubro,
                tipo=c.tipo,
                empresa_nombre=c.empresa_nombre,
                sucursal_nombre=c.sucursal_nombre,
                nro_serie=c.nro_serie,
                fecha_cierre=c.fecha_cierre,
                costo_servicio_cobrado=c.costo_servicio_cobrado,
                cant_km_cobrado=c.cant_km_cobrado,
                costo_km_cobrado=c.costo_km_cobrado,
                total_viaje_cobrado=c.total_viaje_cobrado,
                costo_total_cobrado=c.costo_total_cobrado,
                pasa_it=c.pasa_it,
            )

    async def delete_by_ids(self, incidente_ids: Sequence[UUID]) -> int:
        eliminados = 0
        for incidente_id in incidente_ids:
            if self.rows.pop(incidente_id, None) is not None:
                eliminados += 1
        return eliminados

    async def update_estado_validacion(self, incidente_id: UUID, estado: str) -> None:
        row = self.rows.get(incidente_id)
        if row is not None:
            self.rows[incidente_id] = dataclasses.replace(row, estado_validacion=estado)


class FakeAlertaRepository:
    def __init__(self) -> None:
        self.por_liquidacion: dict[UUID, list[Alerta]] = {}

    async def list_by_liquidacion(self, liquidacion_id: UUID) -> list[Alerta]:
        return self.por_liquidacion.get(liquidacion_id, [])

    async def replace_for_liquidacion(
        self, liquidacion_id: UUID, alertas: Sequence[AlertaConciliada]
    ) -> list[Alerta]:
        creadas = [
            Alerta(
                id=uuid.uuid4(),
                incidente_id=c.generada.incidente_id,
                liquidacion_id=liquidacion_id,
                tipo_alerta=c.generada.tipo_alerta,
                descripcion=c.generada.descripcion,
                datos_contexto=c.generada.datos_contexto,
                riesgo=c.generada.riesgo,
                estado=c.estado,
                justificacion=c.justificacion,
                fecha_generacion=datetime(2026, 1, 1),
            )
            for c in alertas
        ]
        self.por_liquidacion[liquidacion_id] = creadas
        return creadas

    async def update_estado(
        self, liquidacion_id: UUID, alerta_id: UUID, *, estado: str, justificacion: str | None
    ) -> Alerta | None:
        filas = self.por_liquidacion.get(liquidacion_id, [])
        for i, alerta in enumerate(filas):
            if alerta.id == alerta_id:
                actualizada = dataclasses.replace(
                    alerta, estado=estado, justificacion=justificacion
                )
                filas[i] = actualizada
                return actualizada
        return None


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
