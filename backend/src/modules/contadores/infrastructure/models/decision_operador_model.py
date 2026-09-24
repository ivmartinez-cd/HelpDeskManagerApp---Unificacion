from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infrastructure.database.base import Base


class DecisionOperadorModel(Base):
    """Última acción del operador sobre un (proceso, equipo, clase) — lo que el
    legacy relee de su auditoría al cargar la grilla para restaurar el trabajo
    en curso (`GetUltimasDecisionesProcesoAsync`). Una fila por clave, se pisa
    en cada acción. Complementa, no reemplaza, `contadores_estim_log`
    (append-only). Tanto el modo real como el de ejemplo (con
    `NRO_PROCESO_EJEMPLO`) guardan acá.

    No guarda el valor estimado: `accion` + los insumos de la P/L manual
    (`partida_*`/`llegada_*`, con `ID_Contador` para releerlas de Siges)
    alcanzan para volver a correr el motor con los datos del día."""

    __tablename__ = "contadores_decision_operador"

    nro_proceso: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_maquina: Mapped[int] = mapped_column(Integer, primary_key=True)
    clase: Mapped[str] = mapped_column(String(10), primary_key=True)
    accion: Mapped[str] = mapped_column(String(30), nullable=False)
    partida_id_contador: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partida_fecha: Mapped[date | None] = mapped_column(Date, nullable=True)
    partida_valor: Mapped[float | None] = mapped_column(
        Numeric(18, 2, asdecimal=False), nullable=True
    )
    partida_tipo_toma: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partida_para_facturar: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    llegada_id_contador: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llegada_fecha: Mapped[date | None] = mapped_column(Date, nullable=True)
    llegada_valor: Mapped[float | None] = mapped_column(
        Numeric(18, 2, asdecimal=False), nullable=True
    )
    llegada_tipo_toma: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llegada_para_facturar: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
