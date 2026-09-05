from src.modules.contadores.domain.value_objects.estimacion.fuente_estimacion import Coloreo

FACTOR_ALTO = 1.4
FACTOR_BAJO = 0.6


def resolver_coloreo(impresiones: float | None, prom_6_facturados: float | None) -> Coloreo | None:
    """Coloreo bidireccional contra el promedio de impresiones facturadas de
    los últimos 6 procesos cerrados (REGLAS_DE_NEGOCIO §7.2). `None` cuando
    no hay promedio de referencia, o cuando el motor decide excluir el caso
    (Backup sin T4 / En tránsito: Impresiones=0 no es una anomalía ahí)."""
    if impresiones is None or not prom_6_facturados:
        return None
    if impresiones > FACTOR_ALTO * prom_6_facturados:
        return "AZUL"
    if impresiones < FACTOR_BAJO * prom_6_facturados:
        return "NARANJA"
    return "NORMAL"
