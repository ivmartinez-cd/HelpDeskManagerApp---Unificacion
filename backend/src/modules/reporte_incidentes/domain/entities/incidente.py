from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Empresa:
    """Cliente de Canal Directo tal como lo lista `getEmpresas` de wsAyC."""

    id: str
    nombre: str


@dataclass(frozen=True, slots=True)
class Trabajo:
    """Una instancia de la bitácora del técnico (`getIncidentInstances`)."""

    descripcion: str
    observ: str | None = None
    fecha: str | None = None
    estado: str | None = None
    tecnico: str | None = None


@dataclass(frozen=True, slots=True)
class Incidente:
    """Incidente cerrado de un cliente, ya enriquecido con su bitácora y detalle.

    `fecha`/`fecha_cierre` van en ISO `AAAA-MM-DD` ("" si el servicio no la trae).
    `categoria`/`subcategoria` los completa la tipificación (None = sin tipificar
    todavía); `descripcion` es la que se manda a la IA (motivo + observación de
    apertura)."""

    id: str
    numero: str
    fecha: str
    empresa_id: str
    empresa_nombre: str
    descripcion: str
    sucursal: str | None = None
    maquina: str | None = None
    estado: str | None = None
    costo: float | None = None
    solicitante: str | None = None
    tecnico: str | None = None
    tipo_trabajo: str | None = None
    causa: str | None = None
    articulo: str | None = None
    fecha_cierre: str | None = None
    solucion: str | None = None
    trabajos: tuple[Trabajo, ...] = field(default_factory=tuple)
    categoria: str | None = None
    subcategoria: str | None = None


@dataclass(frozen=True, slots=True)
class DetalleIncidente:
    """Lo que agrega `getIncidentById` y no viene en el listado."""

    causa: str | None = None
    tecnico: str | None = None
    fecha_cierre: str | None = None
    tipo_trabajo: str | None = None
