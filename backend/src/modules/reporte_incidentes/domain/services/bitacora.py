"""Reglas del legacy para leer la bitácora del técnico (`getIncidentInstances`)
y el número de incidente. Puras: el adapter SOAP solo entrega las filas."""

from src.modules.reporte_incidentes.domain.entities.incidente import Trabajo

_ESTADOS_FINALES = frozenset({"finalizado", "resuelto", "cerrado"})
_ESTADOS_APERTURA = frozenset({"pendiente", "ingresado", "abierto", "creado"})
ESTADOS_CERRADOS = frozenset({"Resuelto", "Cerrado"})


def digito_verificador(numero: str) -> str:
    """Pesos alternados 3/1 (EAN/UPC) sobre los dígitos, mod 10. "" si no hay dígitos."""
    digitos = [int(c) for c in numero if c.isdigit()]
    if not digitos:
        return ""
    suma = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(digitos))
    return str((10 - suma % 10) % 10)


def numero_con_digito(numero: str) -> str:
    digito = digito_verificador(numero)
    return f"{numero}-{digito}" if digito else numero


def _estado(trabajo: Trabajo) -> str:
    return (trabajo.estado or "").lower()


def derivar_solucion(trabajos: list[Trabajo]) -> str | None:
    """Tareas de las instancias finales unidas con " · "; si ninguna tiene
    descripción, las de todas las instancias. None si no hay nada."""
    finales = [t.descripcion for t in trabajos if _estado(t) in _ESTADOS_FINALES and t.descripcion]
    elegidas = finales or [t.descripcion for t in trabajos if t.descripcion]
    return " · ".join(elegidas) if elegidas else None


def observacion_de_apertura(trabajos: list[Trabajo]) -> str | None:
    """La observación del cliente sale solo de la instancia de apertura (para no
    arrastrar notas de derivación); si no hay, de la primera instancia."""
    apertura = next((t for t in trabajos if _estado(t) in _ESTADOS_APERTURA), None)
    if apertura is not None and apertura.observ:
        return apertura.observ
    return trabajos[0].observ if trabajos else None


def descripcion_completa(motivo: str, observacion: str | None) -> str:
    """"Motivo — observación", sin repetir la observación si ya está en el motivo."""
    if not observacion or observacion in motivo:
        return motivo
    return f"{motivo} — {observacion}" if motivo else observacion
