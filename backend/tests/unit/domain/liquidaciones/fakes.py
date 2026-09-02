"""Fakes en memoria de los puertos de liquidaciones — para tests de casos de uso.

Los fakes del agregado Liquidación (Liquidacion/Incidente/Alerta/Observacion)
viven en `fakes_liquidacion.py` — separados de acá por tamaño (§4)."""

import dataclasses
import uuid
from datetime import date, datetime
from uuid import UUID

from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.regla_alerta import ReglaAlerta
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.value_objects.cd_liquidacion import (
    CdIncidenteRow,
    CdLiquidacion,
    CdLiquidacionDetalle,
)
from src.modules.liquidaciones.domain.value_objects.incidente_importado import (
    ResultadoImportacion,
)


class FakePrestadorRepository:
    def __init__(self, rows: dict[UUID, Prestador] | None = None) -> None:
        self.rows = rows or {}

    async def get_by_id(self, prestador_id: UUID) -> Prestador | None:
        return self.rows.get(prestador_id)

    async def get_by_nombre_corto(self, nombre_corto: str) -> Prestador | None:
        return next((p for p in self.rows.values() if p.nombre_corto == nombre_corto), None)

    async def list_con_cd_id(self) -> list[Prestador]:
        return [p for p in self.rows.values() if p.cd_prestador_id is not None and p.activo]

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


class FakeReglaAlertaRepository:
    def __init__(self, activas: dict[str, ReglaAlerta] | None = None) -> None:
        self.activas = activas or {}

    async def list_activas(self) -> dict[str, ReglaAlerta]:
        return {c: r for c, r in self.activas.items() if r.activa}

    async def list_all(self) -> list[ReglaAlerta]:
        return list(self.activas.values())

    async def set_activa(self, codigo: str, activa: bool) -> ReglaAlerta | None:
        regla = self.activas.get(codigo)
        if regla is None:
            return None
        actualizada = dataclasses.replace(regla, activa=activa)
        self.activas[codigo] = actualizada
        return actualizada


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


class FakeCdLiquidacionesGateway:
    """Gateway en memoria para tests — registra llamadas y permite simular fallos."""

    def __init__(self) -> None:
        self.estados_seteados: list[tuple[int, str, str]] = []  # (ayc_id, estado, usuario)
        self.anulados: list[int] = []
        self.set_estado_raises: Exception | None = None
        self.void_raises: Exception | None = None
        self.liquidaciones_por_empresa: dict[int, list[CdLiquidacion]] = {}
        self.detalles_por_liquidacion: dict[int, CdLiquidacionDetalle] = {}
        self.detalle_falla: set[int] = set()

    async def get_liquidaciones(self, empresa_cd_id: int, top: int = 200) -> list[CdLiquidacion]:
        return self.liquidaciones_por_empresa.get(empresa_cd_id, [])

    async def get_incidentes(self, liquidacion_id: int) -> list[CdIncidenteRow]:
        return []

    async def get_detalle(self, liquidacion_ayc_id: int) -> CdLiquidacionDetalle | None:
        """Default: `CdLiquidacionDetalle` vacío (todo `None`) — igual que AyC
        cuando no hay extra ni factura cargados. `detalle_falla` simula el
        fallo SOAP real (`get_detalle` en `None`)."""
        if liquidacion_ayc_id in self.detalle_falla:
            return None
        return self.detalles_por_liquidacion.get(
            liquidacion_ayc_id,
            CdLiquidacionDetalle(concepto_extra=None, monto_extra=None, numero_factura=None),
        )

    async def set_estado(self, liquidacion_ayc_id: int, nuevo_estado: str, usuario: str) -> None:
        if self.set_estado_raises is not None:
            raise self.set_estado_raises
        self.estados_seteados.append((liquidacion_ayc_id, nuevo_estado, usuario))

    async def void_liquidacion(self, liquidacion_ayc_id: int) -> None:
        if self.void_raises is not None:
            raise self.void_raises
        self.anulados.append(liquidacion_ayc_id)


class FakeNotificador:
    """Registra las liquidaciones notificadas en vez de mandar mail — para
    verificar en los tests que se invoca (y con qué) sin depender de SMTP."""

    def __init__(self) -> None:
        self.aprobaciones: list[Liquidacion] = []

    async def notificar_aprobacion(self, liquidacion: Liquidacion) -> None:
        self.aprobaciones.append(liquidacion)


class FakeLiquidacionFileParser:
    """Devuelve un `ResultadoImportacion` fijo sin pasar por pandas/lxml."""

    def __init__(self, resultado: ResultadoImportacion) -> None:
        self.resultado = resultado
        self.calls: list[tuple[bytes, str]] = []

    def parse(self, contenido: bytes, nombre_archivo: str) -> ResultadoImportacion:
        self.calls.append((contenido, nombre_archivo))
        return self.resultado
