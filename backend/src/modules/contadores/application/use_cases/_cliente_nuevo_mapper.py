from src.modules.contadores.application.dtos.cliente_nuevo_dtos import (
    ClienteNuevoRequest,
    ClienteNuevoResult,
)
from src.modules.contadores.domain.entities.cliente_nuevo import (
    ClienteNuevo,
    ResumenSigesClienteNuevo,
    listo_para_stc,
)


def to_cliente_nuevo_result(
    ficha: ClienteNuevo, siges: ResumenSigesClienteNuevo | None
) -> ClienteNuevoResult:
    return ClienteNuevoResult(
        id=ficha.id,
        cliente=ficha.cliente,
        siges_empresa_id=ficha.siges_empresa_id,
        contrato_nro=ficha.contrato_nro,
        fecha_firma=ficha.fecha_firma,
        vendedor=ficha.vendedor,
        operador_id=ficha.operador_id,
        implementacion_servicio=ficha.implementacion_servicio,
        fecha_estimada_implementacion=ficha.fecha_estimada_implementacion,
        fecha_estimada_primera_facturacion=ficha.fecha_estimada_primera_facturacion,
        dia_corte=ficha.dia_corte,
        equipos_previstos=ficha.equipos_previstos,
        estado=ficha.estado,
        stc_enviado_el=ficha.stc_enviado_el,
        notas=ficha.notas,
        created_at=ficha.created_at,
        updated_at=ficha.updated_at,
        siges=siges,
        listo_para_stc=listo_para_stc(ficha, siges),
    )


def aplicar_request(ficha: ClienteNuevo, request: ClienteNuevoRequest) -> None:
    """Copia los campos editables del request sobre la ficha y revalida."""
    ficha.cliente = request.cliente.strip()
    ficha.siges_empresa_id = request.siges_empresa_id
    ficha.contrato_nro = _limpio(request.contrato_nro)
    ficha.fecha_firma = request.fecha_firma
    ficha.vendedor = _limpio(request.vendedor)
    ficha.operador_id = _limpio(request.operador_id)
    ficha.implementacion_servicio = _limpio(request.implementacion_servicio)
    ficha.fecha_estimada_implementacion = request.fecha_estimada_implementacion
    ficha.fecha_estimada_primera_facturacion = request.fecha_estimada_primera_facturacion
    ficha.dia_corte = request.dia_corte
    ficha.equipos_previstos = request.equipos_previstos
    ficha.estado = request.estado
    ficha.stc_enviado_el = request.stc_enviado_el
    ficha.notas = _limpio(request.notas)
    ficha.validar()


def _limpio(valor: str | None) -> str | None:
    if valor is None:
        return None
    return valor.strip() or None
