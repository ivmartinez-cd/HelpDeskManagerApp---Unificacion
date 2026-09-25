from pydantic import BaseModel, ConfigDict, Field


class ResultadoIASchema(BaseModel):
    """Resultado de una corrida de tipificación con IA. `tipificados` = 0 con
    `fallidos` > 0 es el "IA saturada" del legacy (la pantalla ofrece reintentar).
    Tokens y costo NO viajan al navegador (decisión de Iván, 2026-09-25, igual que
    el legacy): quedan solo en el log del backend (`ia_costo`)."""

    model_config = ConfigDict(from_attributes=True)

    casos: int
    tipificados: int
    fallidos: int
    llamadas: int


class CorreccionRequest(BaseModel):
    """El caso se identifica por su contenido (descripción + causa + solución),
    igual que la clave de la caché: la corrección vale para todo incidente con el
    mismo contenido."""

    descripcion: str = Field(min_length=1)
    causa: str | None = None
    solucion: str | None = None
    categoria: str = Field(min_length=1)
    subcategoria: str = Field(min_length=1)


class CategoriaRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    descripcion: str = Field(min_length=1)
    subcategorias: list[str] = Field(default_factory=list, max_length=60)


class CategoriaDetalleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    nombre: str
    color: str
    descripcion: str
    subcategorias: list[str]
