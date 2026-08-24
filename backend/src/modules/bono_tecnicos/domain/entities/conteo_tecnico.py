from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ConteoTecnico:
    """Cantidad de incidentes por categoría de un técnico en un período —
    equivalente a una fila del resumen `Lista!I1:J9` del Excel "Tecnicos.xlsx"
    que este módulo reemplaza, sin los dos campos de carga manual (Días y
    Tareas Varias) que todavía no tienen fuente de datos propia."""

    tecnico: str
    id_tecnico: int
    periodo: int
    correctivo: int
    preventivo: int
    inst_des: int
    pre_correctivo: int
    entrega_insumos: int
