"""Enriquecimiento de la línea de tiempo de un equipo (MODELO_DE_DATOS.md
§3.6, paridad con `SiGesRepository.GetHistorialEquipoAsync` del legacy):
Delta entre lecturas consecutivas, clasificación de T8/T13 (cambio de
empresa/anexo, ingreso/egreso) y divisorias de ubicación para la tabla del
modal. Lógica pura de dominio — sin acceso a datos."""

from dataclasses import dataclass, replace
from datetime import date

from src.modules.contadores.domain.ports.historial_equipo_port import LecturaHistorialSiges
from src.modules.contadores.domain.value_objects import tipo_toma


@dataclass(frozen=True, slots=True)
class LecturaHistorial:
    fecha: date
    valor: float
    id_tipo_toma: int
    tipo_toma_desc: str
    para_facturar: bool
    fc_nro_proceso: int | None
    fc_periodo_hasta: date | None
    fc_impresiones: float | None
    fc_periodo_facturacion: str | None
    es_fc: bool
    delta: float | None = None
    es_ingreso: bool = False
    es_egreso: bool = False
    es_cambio_empresa: bool = False
    es_cambio_anexo: bool = False
    cambio_empresa_vs_anterior: bool = False
    cambio_sucursal_vs_anterior: bool = False
    cambio_anexo_vs_anterior: bool = False


def enriquecer_historial(crudo_desc: list[LecturaHistorialSiges]) -> list[LecturaHistorial]:
    """`crudo_desc` viene más reciente primero (orden del SQL). Se invierte
    para calcular Delta y clasificar T8/T13 en orden cronológico, y se
    vuelve a invertir al final (orden esperado por el modal)."""
    crudo_asc = list(reversed(crudo_desc))
    base_asc = [
        _base_de(lec, delta) for lec, delta in zip(crudo_asc, _deltas(crudo_asc), strict=True)
    ]
    clasificadas_asc = _con_clasificacion_t8_t13(crudo_asc, base_asc)
    return _con_divisorias(crudo_desc, list(reversed(clasificadas_asc)))


def _base_de(lec: LecturaHistorialSiges, delta: float | None) -> LecturaHistorial:
    return LecturaHistorial(
        fecha=lec.fecha,
        valor=lec.valor,
        id_tipo_toma=lec.id_tipo_toma,
        tipo_toma_desc=lec.tipo_toma_desc,
        para_facturar=lec.para_facturar,
        fc_nro_proceso=lec.fc_nro_proceso,
        fc_periodo_hasta=lec.fc_periodo_hasta,
        fc_impresiones=lec.fc_impresiones,
        fc_periodo_facturacion=lec.fc_periodo_facturacion,
        es_fc=lec.id_factura > 0,
        delta=delta,
    )


def _deltas(asc: list[LecturaHistorialSiges]) -> list[float | None]:
    """No calculamos Delta para Iniciales/Finales/Reiniciales: rompen
    continuidad del contador."""
    deltas: list[float | None] = []
    valor_previo: float | None = None
    for lec in asc:
        if valor_previo is None or tipo_toma.es_inicial_final(lec.id_tipo_toma):
            deltas.append(None)
        else:
            deltas.append(lec.valor - valor_previo)
        valor_previo = lec.valor
    return deltas


def _clasificar_cambio(
    curr: LecturaHistorialSiges, vecina: LecturaHistorialSiges
) -> tuple[bool, bool]:
    """Cambio de empresa gana sobre cambio de anexo. Si algún snapshot es
    NULL, no se dispara ninguno (cae a "Apertura"/"Cierre" en el frontend)."""
    if curr.snap_id_empresa is None or vecina.snap_id_empresa is None:
        return False, False
    if curr.snap_id_empresa != vecina.snap_id_empresa:
        return True, False
    cambio_anexo = (
        curr.snap_id_anexo is not None
        and vecina.snap_id_anexo is not None
        and curr.snap_id_anexo != vecina.snap_id_anexo
    )
    return False, cambio_anexo


def _con_clasificacion_t8_t13(
    crudo_asc: list[LecturaHistorialSiges], base_asc: list[LecturaHistorial]
) -> list[LecturaHistorial]:
    """Para cada T8 (Inicial) se mira la lectura ANTERIOR en el tiempo; para
    cada T13 (Final), la SIGUIENTE. Sin vecina → ingreso/egreso del equipo."""
    resultado = list(base_asc)
    for i, crudo in enumerate(crudo_asc):
        if crudo.id_tipo_toma == tipo_toma.CONTADOR_INICIAL:
            vecina = crudo_asc[i - 1] if i > 0 else None
            resultado[i] = _clasificar(resultado[i], crudo, vecina, es_final=False)
        elif crudo.id_tipo_toma == tipo_toma.CONTADOR_FINAL:
            vecina = crudo_asc[i + 1] if i + 1 < len(crudo_asc) else None
            resultado[i] = _clasificar(resultado[i], crudo, vecina, es_final=True)
    return resultado


def _clasificar(
    lectura: LecturaHistorial,
    crudo: LecturaHistorialSiges,
    vecina: LecturaHistorialSiges | None,
    *,
    es_final: bool,
) -> LecturaHistorial:
    if vecina is None:
        return replace(lectura, es_egreso=True) if es_final else replace(lectura, es_ingreso=True)
    cambio_empresa, cambio_anexo = _clasificar_cambio(crudo, vecina)
    return replace(lectura, es_cambio_empresa=cambio_empresa, es_cambio_anexo=cambio_anexo)


@dataclass(frozen=True, slots=True)
class _Divisoria:
    empresa: bool
    sucursal: bool
    anexo: bool

    @property
    def hay_cambio(self) -> bool:
        return self.empresa or self.sucursal or self.anexo


def _divisoria_de(nueva: LecturaHistorialSiges, vieja: LecturaHistorialSiges) -> _Divisoria:
    """Prioridad empresa > sucursal > anexo — un cambio de empresa implica
    también sucursal/anexo distintos, una sola línea alcanza."""
    empresa = _distinto(nueva.snap_id_empresa, vieja.snap_id_empresa)
    sucursal = not empresa and _distinto(nueva.snap_id_sucursal, vieja.snap_id_sucursal)
    anexo = not empresa and not sucursal and _distinto(nueva.snap_id_anexo, vieja.snap_id_anexo)
    return _Divisoria(empresa, sucursal, anexo)


def _con_divisorias(
    crudo_desc: list[LecturaHistorialSiges], base_desc: list[LecturaHistorial]
) -> list[LecturaHistorial]:
    """Compara cada lectura con la inmediatamente MÁS VIEJA (índice i+1 en la
    lista DESC), igual criterio que `GetCandidatosAsync`. Marca la fila que
    "abre" un segmento de empresa/sucursal/anexo distinto — el frontend
    dibuja la línea debajo de ella."""
    resultado = list(base_desc)
    for i in range(len(resultado) - 1):
        d = _divisoria_de(crudo_desc[i], crudo_desc[i + 1])
        if d.hay_cambio:
            resultado[i] = replace(
                resultado[i],
                cambio_empresa_vs_anterior=d.empresa,
                cambio_sucursal_vs_anterior=d.sucursal,
                cambio_anexo_vs_anterior=d.anexo,
            )
    return resultado


def _distinto(a: int | None, b: int | None) -> bool:
    return a is not None and b is not None and a != b
