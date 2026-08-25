"""Contadores del sync de liquidaciones desde Canal Directo: se acumulan por
prestador en `SincronizarLiquidaciones` y se vuelcan al DTO de resultado."""

from dataclasses import dataclass

from src.modules.liquidaciones.application.dtos.sincronizar_liquidaciones import (
    SincronizarLiquidacionesResultado,
)
from src.modules.liquidaciones.application.use_cases._reconciliar_liquidacion import (
    ReconciliarLiquidacionResultado,
)


@dataclass
class Contadores:
    creadas: int = 0
    ya_existentes: int = 0
    fallidas: int = 0
    anuladas: int = 0
    reconciliadas: int = 0
    estados_actualizados: int = 0
    periodos_actualizados: int = 0
    extras_actualizados: int = 0
    facturas_actualizadas: int = 0

    def registrar_reconciliacion(
        self, resultado: ReconciliarLiquidacionResultado | None
    ) -> None:
        """None o `reconciliada=False` no cuentan: no se intentó o un guard abortó."""
        if resultado is None or not resultado.reconciliada:
            return
        self.reconciliadas += 1
        if resultado.estado_actualizado:
            self.estados_actualizados += 1
        if resultado.periodo_actualizado:
            self.periodos_actualizados += 1
        if resultado.extra_actualizado:
            self.extras_actualizados += 1
        if resultado.factura_actualizada:
            self.facturas_actualizadas += 1

    def sumar(self, otro: "Contadores") -> None:
        self.creadas += otro.creadas
        self.ya_existentes += otro.ya_existentes
        self.fallidas += otro.fallidas
        self.anuladas += otro.anuladas
        self.reconciliadas += otro.reconciliadas
        self.estados_actualizados += otro.estados_actualizados
        self.periodos_actualizados += otro.periodos_actualizados
        self.extras_actualizados += otro.extras_actualizados
        self.facturas_actualizadas += otro.facturas_actualizadas

    def a_resultado(self, *, sin_prestador: int) -> SincronizarLiquidacionesResultado:
        return SincronizarLiquidacionesResultado(
            creadas=self.creadas,
            ya_existentes=self.ya_existentes,
            sin_prestador=sin_prestador,
            fallidas=self.fallidas,
            anuladas=self.anuladas,
            reconciliadas=self.reconciliadas,
            estados_actualizados=self.estados_actualizados,
            periodos_actualizados=self.periodos_actualizados,
            extras_actualizados=self.extras_actualizados,
            facturas_actualizadas=self.facturas_actualizadas,
        )
