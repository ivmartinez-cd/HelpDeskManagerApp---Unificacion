"""Caso de uso ImportarPrestadorMaestro — port de POST /prestadores/importar-excel.

Resuelve/crea Prestador+SPSTs+Tarifarios+TablaKM a partir de un único Excel maestro
ya parseado por el puerto `PrestadorMaestroFileParser`. El parser dedupea
Tarifarios solo dentro del archivo; acá se dedupea además contra lo ya persistido
(clave de 3 partes: tipo+costo+vigencia) — sin este segundo dedup, re-importar el
mismo archivo crea tarifarios duplicados en cada corrida. Prestador/SPST existentes
nunca se actualizan (igual que el legacy), Tabla KM existente (por empresa+sucursal)
se omite en vez de pisarse.

Tras crear tarifarios se recadenan las vigencias de cada grupo (tipo_servicio,
zona=None) que recibió filas nuevas — divergencia consciente vs. el legacy, que al
importar dejaba vigencias solapadas (ver `domain/services/cadena_tarifaria.py`)."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.modules.liquidaciones.application.dtos.importar_prestador_maestro import (
    ImportarPrestadorMaestroResultado,
)
from src.modules.liquidaciones.application.use_cases._recadenado import recadenar_grupo
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario
from src.modules.liquidaciones.domain.repositories.prestador_maestro_file_parser import (
    PrestadorMaestroFileParser,
)
from src.modules.liquidaciones.domain.repositories.prestador_repository import (
    PrestadorRepository,
)
from src.modules.liquidaciones.domain.repositories.spst_repository import SpstRepository
from src.modules.liquidaciones.domain.repositories.tabla_km_repository import TablaKmRepository
from src.modules.liquidaciones.domain.repositories.tarifario_repository import (
    TarifarioRepository,
)
from src.modules.liquidaciones.domain.services.importacion_maestro.matching import matchear_spst
from src.modules.liquidaciones.domain.value_objects.prestador_maestro_importado import (
    SpstImportado,
    TablaKmImportada,
    TarifarioImportado,
)


@dataclass(frozen=True)
class ImportarPrestadorMaestroPorts:
    parser: PrestadorMaestroFileParser
    prestadores: PrestadorRepository
    spsts: SpstRepository
    tarifarios: TarifarioRepository
    tabla_km: TablaKmRepository


class ImportarPrestadorMaestro:
    def __init__(self, ports: ImportarPrestadorMaestroPorts) -> None:
        self._ports = ports

    async def execute(
        self, *, contenido: bytes, nombre_archivo: str
    ) -> ImportarPrestadorMaestroResultado:
        resultado = self._ports.parser.parse(contenido, nombre_archivo)

        prestador, creado = await self._resolver_prestador(resultado.nombre_corto)
        spsts_por_nombre, spsts_creados = await self._resolver_spsts(prestador, resultado.spsts)
        tarifarios_creados, tarifarios_omitidos = await self._crear_tarifarios(
            prestador, resultado.tarifarios
        )
        tabla_km_creadas, tabla_km_omitidas = await self._crear_tabla_km(
            prestador, resultado.tabla_km, spsts_por_nombre
        )

        return ImportarPrestadorMaestroResultado(
            prestador_id=prestador.id,
            prestador_creado=creado,
            spsts_creados=spsts_creados,
            tarifarios_creados=tarifarios_creados,
            tarifarios_omitidos=tarifarios_omitidos,
            tabla_km_creadas=tabla_km_creadas,
            tabla_km_omitidas=tabla_km_omitidas,
            hoja_tabla_km=resultado.hoja_tabla_km,
        )

    async def _resolver_prestador(self, nombre_corto: str) -> tuple[Prestador, bool]:
        # `.strip().upper()`: los otros 2 caminos de escritura de Prestador
        # (Create/UpdatePrestador de config_prestadores.py, import CSV) normalizan
        # igual antes de comparar — get_by_nombre_corto es `==` case-sensitive, sin
        # esto "Pentacom" del Excel nunca matchea "PENTACOM" ya en la base.
        clave = nombre_corto.strip().upper()
        existente = await self._ports.prestadores.get_by_nombre_corto(clave)
        if existente is not None:
            return existente, False
        creado = await self._ports.prestadores.create(
            nombre=clave, nombre_corto=clave, cuit=None, region=None
        )
        return creado, True

    async def _resolver_spsts(
        self, prestador: Prestador, spsts: list[SpstImportado]
    ) -> tuple[dict[str, Spst], int]:
        existentes = await self._ports.spsts.list_by_prestador(prestador.id)
        por_nombre = {s.nombre.strip().lower(): s for s in existentes}
        creados = 0
        for spst in spsts:
            clave = spst.nombre.strip().lower()
            if clave in por_nombre:
                continue
            nuevo = await self._ports.spsts.create(
                prestador_id=prestador.id,
                nombre=spst.nombre,
                domicilio=None,
                localidad=None,
                provincia=None,
                zona=None,
            )
            por_nombre[clave] = nuevo
            creados += 1
        return por_nombre, creados

    async def _crear_tarifarios(
        self, prestador: Prestador, tarifarios: list[TarifarioImportado]
    ) -> tuple[int, int]:
        existentes = await self._ports.tarifarios.list_by_prestador(prestador.id)
        vistos = {self._clave_tarifario(t) for t in existentes}
        creados = omitidos = 0
        tipos_creados: set[str] = set()
        for t in tarifarios:
            clave = self._clave_tarifario(t)
            if clave in vistos:
                omitidos += 1
                continue
            await self._crear_un_tarifario(prestador.id, t)
            vistos.add(clave)
            tipos_creados.add(t.tipo_servicio)
            creados += 1
        await self._recadenar_tipos_creados(prestador.id, tipos_creados)
        return creados, omitidos

    async def _recadenar_tipos_creados(self, prestador_id: UUID, tipos: set[str]) -> None:
        # El maestro crea todo con zona=None → el grupo afectado es (prestador, tipo, None).
        for tipo in sorted(tipos):
            await recadenar_grupo(
                self._ports.tarifarios, prestador_id=prestador_id, tipo_servicio=tipo, zona=None
            )

    @staticmethod
    def _clave_tarifario(t: Tarifario | TarifarioImportado) -> tuple[str, float, date]:
        return t.tipo_servicio, round(t.costo_servicio, 2), t.vigencia_desde

    async def _crear_un_tarifario(self, prestador_id: UUID, t: TarifarioImportado) -> None:
        await self._ports.tarifarios.create(
            prestador_id=prestador_id,
            tipo_servicio=t.tipo_servicio,
            zona=None,
            costo_servicio=t.costo_servicio,
            costo_km=t.costo_km,
            vigencia_desde=t.vigencia_desde,
            vigencia_hasta=None,
        )

    async def _crear_tabla_km(
        self,
        prestador: Prestador,
        filas: list[TablaKmImportada],
        spsts_por_nombre: dict[str, Spst],
    ) -> tuple[int, int]:
        existentes = await self._ports.tabla_km.list_by_prestador(prestador.id)
        vistos = {self._clave_tabla_km(t.empresa_nombre, t.sucursal_nombre) for t in existentes}
        nombres_spst = [s.nombre for s in spsts_por_nombre.values()]
        creadas = omitidas = 0
        for fila in filas:
            clave = self._clave_tabla_km(fila.empresa_nombre, fila.sucursal_nombre)
            if clave in vistos:
                omitidas += 1
                continue
            spst_id = self._resolver_spst_id(fila.spst_nombre, nombres_spst, spsts_por_nombre)
            await self._crear_una_tabla_km(prestador.id, fila, spst_id)
            vistos.add(clave)
            creadas += 1
        return creadas, omitidas

    @staticmethod
    def _clave_tabla_km(empresa: str, sucursal: str) -> tuple[str, str]:
        return empresa.strip().lower(), sucursal.strip().lower()

    @staticmethod
    def _resolver_spst_id(
        spst_nombre: str | None, nombres: list[str], por_nombre: dict[str, Spst]
    ) -> UUID | None:
        matcheado = matchear_spst(spst_nombre, nombres)
        if matcheado is None:
            return None
        return por_nombre[matcheado.strip().lower()].id

    async def _crear_una_tabla_km(
        self, prestador_id: UUID, fila: TablaKmImportada, spst_id: UUID | None
    ) -> None:
        await self._ports.tabla_km.create(
            prestador_id=prestador_id,
            spst_id=spst_id,
            empresa_nombre=fila.empresa_nombre,
            sucursal_nombre=fila.sucursal_nombre,
            observaciones=None,
            domicilio_cliente=fila.domicilio_cliente,
            localidad_cliente=fila.localidad_cliente,
            provincia_cliente=fila.provincia_cliente,
            kms_recorrido=fila.kms_recorrido,
            umbral_viatico=fila.umbral_viatico,
            aplica_viatico=fila.aplica_viatico,
            kms_a_facturar=fila.kms_a_facturar,
            url_maps=fila.url_maps,
        )
