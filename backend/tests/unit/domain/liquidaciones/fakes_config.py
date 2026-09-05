"""Fakes en memoria con los métodos de escritura de los puertos de configuración
(update/toggle_activo/delete, y la cadena de vigencias de tarifarios) — extienden
los fakes base de `fakes.py`, que solo cubren lo que usan los casos de uso de
importación/reanálisis."""

import dataclasses
from datetime import date, datetime
from uuid import UUID, uuid4

from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.entities.tarifario_zona_map import TarifarioZonaMap
from src.modules.liquidaciones.domain.errors import SigesVinculoDuplicadoError
from src.modules.liquidaciones.domain.repositories.siges_catalogo_gateway import (
    SigesCostoServicio,
    SigesEmpresaInfo,
    SigesSucursalCliente,
)
from tests.unit.domain.liquidaciones.fakes import (
    FakePrestadorRepository,
    FakeSpstRepository,
    FakeTablaKmRepository,
    FakeTarifarioRepository,
)


class FakeSigesCatalogoGateway:
    def __init__(
        self,
        empresas: list[SigesEmpresaInfo] | None = None,
        costos: list[SigesCostoServicio] | None = None,
        sucursales: dict[int, list[SigesSucursalCliente]] | None = None,
    ) -> None:
        self.empresas = empresas or []
        self.costos = costos or []
        self.sucursales = sucursales or {}

    async def list_empresas_activas(self) -> list[SigesEmpresaInfo]:
        return list(self.empresas)

    async def list_costos_habilitados(
        self, siges_empresa_ids: list[int]
    ) -> list[SigesCostoServicio]:
        return [c for c in self.costos if c.siges_empresa_id in siges_empresa_ids]

    async def list_sucursales_de_prestador(
        self, siges_empresa_id: int
    ) -> list[SigesSucursalCliente]:
        return list(self.sucursales.get(siges_empresa_id, []))


class FakeTarifarioZonaMapRepository:
    def __init__(self, rows: list[TarifarioZonaMap] | None = None) -> None:
        self.rows = rows or []

    async def list_all(self) -> list[TarifarioZonaMap]:
        return list(self.rows)

    async def upsert(
        self, *, prestador_id: UUID, descripcion_siges: str, spst_id: UUID | None
    ) -> TarifarioZonaMap:
        for i, fila in enumerate(self.rows):
            if (fila.prestador_id, fila.descripcion_siges) == (prestador_id, descripcion_siges):
                self.rows[i] = dataclasses.replace(fila, spst_id=spst_id)
                return self.rows[i]
        nueva = TarifarioZonaMap(
            id=uuid4(),
            prestador_id=prestador_id,
            descripcion_siges=descripcion_siges,
            spst_id=spst_id,
            created_at=datetime(2026, 1, 1),
        )
        self.rows.append(nueva)
        return nueva


class FakeConfigPrestadorRepository(FakePrestadorRepository):
    async def update(
        self,
        prestador_id: UUID,
        *,
        nombre: str,
        nombre_corto: str,
        cuit: str | None,
        region: str | None,
    ) -> Prestador | None:
        row = self.rows.get(prestador_id)
        if row is None:
            return None
        actualizado = dataclasses.replace(
            row, nombre=nombre, nombre_corto=nombre_corto, cuit=cuit, region=region
        )
        self.rows[prestador_id] = actualizado
        return actualizado

    async def toggle_activo(self, prestador_id: UUID, *, activo: bool) -> Prestador | None:
        row = self.rows.get(prestador_id)
        if row is None:
            return None
        actualizado = dataclasses.replace(row, activo=activo)
        self.rows[prestador_id] = actualizado
        return actualizado

    async def vincular_siges(
        self, prestador_id: UUID, *, siges_empresa_id: int | None
    ) -> Prestador | None:
        row = self.rows.get(prestador_id)
        if row is None:
            return None
        if siges_empresa_id is not None and any(
            p.siges_empresa_id == siges_empresa_id and p.id != prestador_id
            for p in self.rows.values()
        ):
            raise SigesVinculoDuplicadoError(siges_empresa_id)
        actualizado = dataclasses.replace(row, siges_empresa_id=siges_empresa_id)
        self.rows[prestador_id] = actualizado
        return actualizado

    async def delete(self, prestador_id: UUID) -> bool:
        return self.rows.pop(prestador_id, None) is not None


class FakeConfigSpstRepository(FakeSpstRepository):
    def _index_of(self, spst_id: UUID) -> int | None:
        return next((i for i, s in enumerate(self.rows) if s.id == spst_id), None)

    async def list_all(
        self, *, prestador_id: UUID | None = None, solo_activos: bool = False
    ) -> list[Spst]:
        rows = [s for s in self.rows if prestador_id is None or s.prestador_id == prestador_id]
        return [s for s in rows if not solo_activos or s.activo]

    async def update(
        self,
        spst_id: UUID,
        *,
        nombre: str,
        domicilio: str | None,
        localidad: str | None,
        provincia: str | None,
        zona_cobertura: str | None,
    ) -> Spst | None:
        idx = self._index_of(spst_id)
        if idx is None:
            return None
        self.rows[idx] = dataclasses.replace(
            self.rows[idx],
            nombre=nombre,
            domicilio=domicilio,
            localidad=localidad,
            provincia=provincia,
            zona_cobertura=zona_cobertura,
        )
        return self.rows[idx]

    async def toggle_activo(self, spst_id: UUID, *, activo: bool) -> Spst | None:
        idx = self._index_of(spst_id)
        if idx is None:
            return None
        self.rows[idx] = dataclasses.replace(self.rows[idx], activo=activo)
        return self.rows[idx]

    async def vincular_siges(self, spst_id: UUID, *, siges_empresa_id: int | None) -> Spst | None:
        idx = self._index_of(spst_id)
        if idx is None:
            return None
        if siges_empresa_id is not None and any(
            s.siges_empresa_id == siges_empresa_id and s.id != spst_id for s in self.rows
        ):
            raise SigesVinculoDuplicadoError(siges_empresa_id)
        self.rows[idx] = dataclasses.replace(self.rows[idx], siges_empresa_id=siges_empresa_id)
        return self.rows[idx]

    async def delete(self, spst_id: UUID) -> bool:
        idx = self._index_of(spst_id)
        if idx is None:
            return False
        del self.rows[idx]
        return True


class FakeConfigTarifarioRepository(FakeTarifarioRepository):
    def _index_of(self, tarifario_id: UUID) -> int | None:
        return next((i for i, t in enumerate(self.rows) if t.id == tarifario_id), None)

    async def get_by_id(self, tarifario_id: UUID) -> Tarifario | None:
        idx = self._index_of(tarifario_id)
        return self.rows[idx] if idx is not None else None

    async def list_grupo(
        self, *, prestador_id: UUID, tipo_servicio: str, spst_id: UUID | None
    ) -> list[Tarifario]:
        return [
            t
            for t in self.rows
            if (t.prestador_id, t.tipo_servicio, t.spst_id)
            == (prestador_id, tipo_servicio, spst_id)
        ]

    async def set_vigencia_hasta(self, tarifario_id: UUID, vigencia_hasta: date | None) -> None:
        idx = self._index_of(tarifario_id)
        if idx is None:
            return
        self.rows[idx] = dataclasses.replace(self.rows[idx], vigencia_hasta=vigencia_hasta)

    async def update(
        self,
        tarifario_id: UUID,
        *,
        prestador_id: UUID,
        tipo_servicio: str,
        spst_id: UUID | None,
        costo_servicio: float,
        costo_km: float,
        vigencia_desde: date,
        vigencia_hasta: date | None,
    ) -> Tarifario | None:
        idx = self._index_of(tarifario_id)
        if idx is None:
            return None
        self.rows[idx] = dataclasses.replace(
            self.rows[idx],
            prestador_id=prestador_id,
            tipo_servicio=tipo_servicio,
            spst_id=spst_id,
            costo_servicio=costo_servicio,
            costo_km=costo_km,
            vigencia_desde=vigencia_desde,
            vigencia_hasta=vigencia_hasta,
        )
        return self.rows[idx]

    async def delete(self, tarifario_id: UUID) -> bool:
        idx = self._index_of(tarifario_id)
        if idx is None:
            return False
        del self.rows[idx]
        return True


class FakeConfigTablaKmRepository(FakeTablaKmRepository):
    def _index_of(self, tabla_km_id: UUID) -> int | None:
        return next((i for i, t in enumerate(self.rows) if t.id == tabla_km_id), None)

    async def get_by_id(self, tabla_km_id: UUID) -> TablaKm | None:
        idx = self._index_of(tabla_km_id)
        return None if idx is None else self.rows[idx]

    async def update_vinculo_spst(
        self, tabla_km_id: UUID, *, spst_id: UUID | None
    ) -> TablaKm | None:
        idx = self._index_of(tabla_km_id)
        if idx is None:
            return None
        self.rows[idx] = dataclasses.replace(self.rows[idx], spst_id=spst_id)
        return self.rows[idx]

    async def update(
        self,
        tabla_km_id: UUID,
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
    ) -> TablaKm | None:
        idx = self._index_of(tabla_km_id)
        if idx is None:
            return None
        self.rows[idx] = dataclasses.replace(
            self.rows[idx],
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
        )
        return self.rows[idx]

    async def delete(self, tabla_km_id: UUID) -> bool:
        idx = self._index_of(tabla_km_id)
        if idx is None:
            return False
        del self.rows[idx]
        return True
