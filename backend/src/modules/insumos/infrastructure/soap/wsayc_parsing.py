"""Parseo puro de las respuestas del wsAyC (JSON serializado dentro de strings SOAP).

Port de los helpers de soap_query.py. El servicio devuelve '{"Supply": {...}}' cuando el
ID existe y '[]' cuando no; los escalares (persistNewSupply) vienen como JSON escalar
(ej. '"441770"' o '"0"' si falló).
"""

import json

from src.modules.insumos.domain.value_objects.cd_supply import CdMachine, CdSupply


def safe_parse(raw: str | None) -> object:
    """Si `raw` no es JSON válido devuelve el string tal cual — los callers descartan
    con isinstance() todo lo que no sea list/dict y les queda el crudo para loguear."""
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def parse_machine(raw: str | None) -> CdMachine | None:
    """None = "[]" (equipo sin asignar a ninguna empresa, candidato a bodega/CD1)."""
    parsed = safe_parse(raw)
    if not isinstance(parsed, dict) or "Machine" not in parsed:
        return None
    machine = parsed["Machine"]
    if not isinstance(machine, dict):
        return None
    return CdMachine(
        familia_id=_text(machine, "familia_id"),
        familia_name=_text(machine, "Familia"),
        empresa_id=_text(machine, "empresa_id"),
        sucursal_id=_text(machine, "sucursal_id"),
    )


def parse_supply_by_id(raw: str | None) -> CdSupply | None:
    parsed = safe_parse(raw)
    if isinstance(parsed, dict) and "Supply" in parsed and isinstance(parsed["Supply"], dict):
        return supply_from_dict(parsed["Supply"])
    if isinstance(parsed, dict) and parsed:
        return supply_from_dict(parsed)
    return None


def parse_top_supplies(raw: str | None) -> list[CdSupply]:
    parsed = safe_parse(raw)
    if not isinstance(parsed, list):
        return []
    return [
        supply_from_dict(item["Supply"])
        for item in parsed
        if isinstance(item, dict) and isinstance(item.get("Supply"), dict)
    ]


def parse_article_parts(raw: str | None) -> dict[str, str]:
    """El SOAP devuelve [{"id","name"}] (el portal devolvía {id: name}) — se normaliza
    acá al dict que espera insumo_matching. Ninguna vía trae `sku` en producción."""
    parsed = safe_parse(raw)
    if not isinstance(parsed, list):
        return {}
    return {
        str(item["id"]): str(item["name"])
        for item in parsed
        if isinstance(item, dict) and "id" in item
    }


def parse_persist_response(raw: str | None) -> int:
    """ID del pedido creado, o 0 si el servicio no confirmó (respuesta '"0"' o basura)."""
    try:
        return int(json.loads(raw or ""))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0


def parse_details_description(raw: str | None) -> str:
    """Campo "Insumo" del primer Detail — la única fuente de la descripción real del
    consumible sin scrapear el portal."""
    parsed = safe_parse(raw)
    if not isinstance(parsed, list):
        return ""
    for item in parsed:
        if isinstance(item, dict) and isinstance(item.get("Detail"), dict):
            return _text(item["Detail"], "Insumo")
    return ""


def supply_from_dict(data: dict[str, object]) -> CdSupply:
    return CdSupply(
        supply_id=_numeric_supply_id(data),
        reference=_text(data, "NroIncidenteCliente"),
        estado=_text(data, "Estado"),
        fecha=_text(data, "Fecha"),
        nro_serie_solicitud=_text(data, "NroSerieSolicitud"),
        nro_serie=_text(data, "NroSerie"),
        sku=_text(data, "NroArticulo"),
        descripcion=_text(data, "Descripcion"),
        solicitante_nombre=_text(data, "Solicitante"),
        solicitante_telefono=_text(data, "TelefonoSolicitante"),
        solicitante_email=_text(data, "EmailSolicitante"),
        destinatario_nombre=_text(data, "EntregaA"),
        destinatario_telefono=_text(data, "TelefonoDestinatario"),
        destinatario_email=_text(data, "EmailDestinatario"),
    )


def _numeric_supply_id(data: dict[str, object]) -> int:
    """El ID puede venir en IdSupply/id/NroPedido y con check digit ("441415-9") —
    0 si no es parseable (los callers lo tratan como fila sin ID usable)."""
    raw_id = data.get("IdSupply") or data.get("id") or data.get("NroPedido") or ""
    try:
        return int(str(raw_id).split("-")[0])
    except (ValueError, TypeError):
        return 0


def _text(data: dict[str, object], key: str) -> str:
    value = data.get(key)
    return str(value).strip() if value is not None else ""
