"""Factories de entidades de liquidaciones para tests — todo con defaults sensatos,
override vía kwargs. Sin DB: las entidades son dataclasses inmutables."""

import uuid
from datetime import date, datetime
from typing import Any

from src.modules.liquidaciones.domain.entities.incidente import Incidente
from src.modules.liquidaciones.domain.entities.liquidacion import Liquidacion
from src.modules.liquidaciones.domain.entities.prestador import Prestador
from src.modules.liquidaciones.domain.entities.regla_alerta import ReglaAlerta
from src.modules.liquidaciones.domain.entities.spst import Spst
from src.modules.liquidaciones.domain.entities.tabla_km import TablaKm
from src.modules.liquidaciones.domain.entities.tarifario import Tarifario

NOW = datetime(2026, 1, 1)


def make_prestador(**overrides: Any) -> Prestador:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "nombre": "Prestador de Prueba",
        "nombre_corto": "TEST",
        "cuit": None,
        "region": None,
        "activo": True,
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return Prestador(**defaults)


def make_spst(**overrides: Any) -> Spst:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "prestador_id": uuid.uuid4(),
        "nombre": "SPST Test",
        "domicilio": None,
        "localidad": None,
        "provincia": None,
        "zona": None,
        "activo": True,
        "created_at": NOW,
    }
    defaults.update(overrides)
    return Spst(**defaults)


def make_tarifario(**overrides: Any) -> Tarifario:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "prestador_id": uuid.uuid4(),
        "tipo_servicio": "correctivo",
        "zona": None,
        "costo_servicio": 1500.0,
        "costo_km": 100.0,
        "vigencia_desde": date(2025, 1, 1),
        "vigencia_hasta": None,
        "created_at": NOW,
    }
    defaults.update(overrides)
    return Tarifario(**defaults)


def make_tabla_km(**overrides: Any) -> TablaKm:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "prestador_id": uuid.uuid4(),
        "spst_id": None,
        "empresa_nombre": "Empresa Test",
        "sucursal_nombre": "Sucursal Test",
        "observaciones": None,
        "domicilio_cliente": None,
        "localidad_cliente": None,
        "provincia_cliente": None,
        "kms_recorrido": 100.0,
        "umbral_viatico": 30.0,
        "aplica_viatico": True,
        "kms_a_facturar": 100.0,
        "url_maps": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return TablaKm(**defaults)


def make_liquidacion(**overrides: Any) -> Liquidacion:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "prestador_id": uuid.uuid4(),
        "numero_liquidacion": "1-1",
        "periodo": "2026-01",
        "tipo_liquidacion": "regular",
        "nombre_archivo": None,
        "fecha_importacion": NOW,
        "estado": "abierta",
        "total_incidentes": 0,
        "total_alertas": 0,
        "total_importe": 0.0,
    }
    defaults.update(overrides)
    return Liquidacion(**defaults)


def make_incidente(**overrides: Any) -> Incidente:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "liquidacion_id": uuid.uuid4(),
        "numero_incidente": "1",
        "rubro": None,
        "tipo": "correctivo",
        "empresa_nombre": "Empresa Test",
        "sucursal_nombre": "Sucursal Test",
        "nro_serie": None,
        "fecha_cierre": date(2026, 1, 15),
        "costo_servicio_cobrado": 1500.0,
        # 0.0 a propósito: cualquier valor >0 sin una TablaKm que lo respalde dispara
        # ALT009 en tests que no están probando ALT009 — los tests de ALT002/ALT003
        # que sí necesitan km cobrado lo pisan explícitamente vía override.
        "cant_km_cobrado": 0.0,
        "costo_km_cobrado": 100.0,
        "total_viaje_cobrado": 10000.0,
        "costo_total_cobrado": 11500.0,
        "pasa_it": True,
        "costo_servicio_esperado": None,
        "cant_km_esperado": None,
        "costo_km_esperado": None,
        "estado_validacion": "pendiente",
    }
    defaults.update(overrides)
    return Incidente(**defaults)


def make_regla(**overrides: Any) -> ReglaAlerta:
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "codigo": "ALT001",
        "nombre": "Regla de prueba",
        "descripcion": None,
        "activa": True,
        "riesgo_base": 100.0,
        "configuracion": {},
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return ReglaAlerta(**defaults)


def reglas_activas_default() -> dict[str, ReglaAlerta]:
    """Baseline sin ALT005 — el contrato de `reglas_activas` en todo el motor es
    "estar en el dict == estar activa" (así lo devolvería
    `ReglaAlertaRepository.list_activas()`, ya filtrado por SQL) — un test que quiera
    ejercitar ALT005 la agrega explícitamente vía `reglas["ALT005"] = make_regla(...)`.
    Nota: en producción real ALT005 SÍ está activa (`activa=True`, distinto del
    default `False` de `seed.py` del legacy) — este baseline sin ALT005 es solo una
    conveniencia para no forzar todos los tests existentes a lidiar con ella, no
    representa el estado real de producción."""
    codigos_activos = {
        "ALT001": 100.0,
        "ALT002": 100.0,
        "ALT003": 80.0,
        "ALT004": 90.0,
        "ALT008": 100.0,
        "ALT009": 80.0,
    }
    return {
        codigo: make_regla(codigo=codigo, riesgo_base=riesgo, activa=True)
        for codigo, riesgo in codigos_activos.items()
    }
