import json
from datetime import datetime

from src.modules.reporte_incidentes.application.use_cases.armar_reporte import (
    PedidoReporte,
    ReporteArmado,
)
from src.modules.reporte_incidentes.domain.entities.categoria import (
    Categoria,
    TipificacionGuardada,
)
from src.modules.reporte_incidentes.domain.entities.incidente import Empresa, Incidente
from src.modules.reporte_incidentes.domain.repositories.clasificador_ia import RespuestaIA
from src.modules.reporte_incidentes.domain.value_objects.periodo import Periodo
from src.shared.domain.errors import ExternalServiceError

TAXONOMIA = [
    Categoria("Medio de Impresion", "#f0a400", "papel", ("Atasco de papel (comun)",)),
]


class FakeCache:
    def __init__(self, inicial: dict[str, TipificacionGuardada] | None = None) -> None:
        self.guardadas = dict(inicial or {})

    async def obtener(self, claves: set[str]) -> dict[str, TipificacionGuardada]:
        return {c: t for c, t in self.guardadas.items() if c in claves}

    async def guardar(self, tipificaciones: dict[str, TipificacionGuardada]) -> None:
        self.guardadas.update(tipificaciones)


class FakeTaxonomia:
    def __init__(self, categorias: list[Categoria] | None = None) -> None:
        self.categorias = list(categorias if categorias is not None else TAXONOMIA)

    async def listar(self) -> list[Categoria]:
        return list(self.categorias)

    async def crear(self, categoria: Categoria) -> None:
        self.categorias.append(categoria)

    async def reemplazar(self, nombre_anterior: str, categoria: Categoria) -> None:
        indice = [c.nombre.lower() for c in self.categorias].index(nombre_anterior.lower())
        self.categorias[indice] = categoria

    async def eliminar(self, nombre: str) -> None:
        self.categorias = [c for c in self.categorias if c.nombre.lower() != nombre.lower()]


class FakeClasificador:
    """Responde "alta" para cada caso del prompt; `falla` simula todos los modelos caídos."""

    def __init__(self, configurado: bool = True, falla: bool = False) -> None:
        self.configurado = configurado
        self.falla = falla
        self.prompts: list[str] = []

    async def clasificar(self, prompt: str) -> RespuestaIA:
        self.prompts.append(prompt)
        if self.falla:
            raise ExternalServiceError("caída")
        casos = [linea for linea in prompt.splitlines() if ". Reporte del cliente:" in linea]
        items = [
            {"i": i, "categoria": "Medio de Impresion",
             "subcategoria": "Atasco de papel (comun)", "confianza": "alta"}
            for i in range(len(casos))
        ]
        return RespuestaIA(json.dumps(items), "fake", 1000, 100)


class FakeArmar:
    def __init__(self, incidentes: list[Incidente]) -> None:
        self.incidentes = incidentes

    async def execute(self, pedido: PedidoReporte) -> ReporteArmado:
        return ReporteArmado(
            Empresa("1", "ACME"), Periodo(2026, 6), 1, [Periodo(2026, 6)],
            self.incidentes, 0, TAXONOMIA, datetime(2026, 6, 30),
        )
