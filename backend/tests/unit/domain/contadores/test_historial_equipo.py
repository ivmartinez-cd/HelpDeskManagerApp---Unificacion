"""Paridad con `SiGesRepository.GetHistorialEquipoAsync` legacy —
Delta, clasificación T8/T13 y divisorias de ubicación (MODELO_DE_DATOS.md
§3.6)."""

from datetime import date

from src.modules.contadores.domain.ports.historial_equipo_port import LecturaHistorialSiges
from src.modules.contadores.domain.services.historial_equipo import enriquecer_historial


def _lectura(
    fecha: date,
    valor: float,
    id_tipo_toma: int = 1,
    id_factura: int = 1,
    snap_id_empresa: int | None = 1,
    snap_id_sucursal: int | None = 1,
    snap_id_anexo: int | None = 1,
) -> LecturaHistorialSiges:
    return LecturaHistorialSiges(
        fecha=fecha,
        valor=valor,
        id_tipo_toma=id_tipo_toma,
        tipo_toma_desc="Real",
        para_facturar=True,
        fc_nro_proceso=None,
        fc_periodo_hasta=None,
        fc_impresiones=None,
        fc_periodo_facturacion=None,
        id_factura=id_factura,
        snap_id_empresa=snap_id_empresa,
        snap_id_sucursal=snap_id_sucursal,
        snap_id_anexo=snap_id_anexo,
    )


def test_delta_entre_dos_reales_consecutivos() -> None:
    # DESC: más reciente primero, igual que el SQL.
    crudo = [_lectura(date(2026, 2, 1), 1500), _lectura(date(2026, 1, 1), 1000)]

    resultado = enriquecer_historial(crudo)

    mas_reciente = next(r for r in resultado if r.fecha == date(2026, 2, 1))
    mas_vieja = next(r for r in resultado if r.fecha == date(2026, 1, 1))
    assert mas_reciente.delta == 500
    assert mas_vieja.delta is None  # primera lectura del período


def test_delta_es_none_para_inicial_final_reinicial() -> None:
    crudo = [
        _lectura(date(2026, 2, 1), 100, id_tipo_toma=8),  # T8 Inicial
        _lectura(date(2026, 1, 1), 900),
    ]

    resultado = enriquecer_historial(crudo)

    t8 = next(r for r in resultado if r.id_tipo_toma == 8)
    assert t8.delta is None


def test_es_fc_solo_cuando_id_factura_mayor_a_cero() -> None:
    crudo = [_lectura(date(2026, 1, 1), 1000, id_factura=0)]

    resultado = enriquecer_historial(crudo)

    assert resultado[0].es_fc is False


def test_es_fc_true_cuando_id_factura_es_positivo() -> None:
    crudo = [_lectura(date(2026, 1, 1), 1000, id_factura=42)]

    resultado = enriquecer_historial(crudo)

    assert resultado[0].es_fc is True


def test_t8_sin_vecina_anterior_es_ingreso() -> None:
    crudo = [_lectura(date(2026, 1, 1), 100, id_tipo_toma=8)]

    resultado = enriquecer_historial(crudo)

    assert resultado[0].es_ingreso is True
    assert resultado[0].es_cambio_empresa is False


def test_t13_sin_vecina_siguiente_es_egreso() -> None:
    crudo = [_lectura(date(2026, 1, 1), 100, id_tipo_toma=13)]

    resultado = enriquecer_historial(crudo)

    assert resultado[0].es_egreso is True


def test_t8_con_vecina_de_otra_empresa_es_cambio_empresa() -> None:
    crudo = [
        _lectura(date(2026, 2, 1), 100, id_tipo_toma=8, snap_id_empresa=2),
        _lectura(date(2026, 1, 1), 900, snap_id_empresa=1),
    ]

    resultado = enriquecer_historial(crudo)

    t8 = next(r for r in resultado if r.id_tipo_toma == 8)
    assert t8.es_cambio_empresa is True
    assert t8.es_cambio_anexo is False
    assert t8.es_ingreso is False


def test_t8_con_vecina_mismo_empresa_otro_anexo_es_cambio_anexo() -> None:
    crudo = [
        _lectura(date(2026, 2, 1), 100, id_tipo_toma=8, snap_id_empresa=1, snap_id_anexo=2),
        _lectura(date(2026, 1, 1), 900, snap_id_empresa=1, snap_id_anexo=1),
    ]

    resultado = enriquecer_historial(crudo)

    t8 = next(r for r in resultado if r.id_tipo_toma == 8)
    assert t8.es_cambio_empresa is False
    assert t8.es_cambio_anexo is True


def test_divisoria_vs_lectura_mas_vieja_marca_cambio_de_sucursal() -> None:
    crudo = [
        _lectura(date(2026, 2, 1), 1500, snap_id_empresa=1, snap_id_sucursal=9),
        _lectura(date(2026, 1, 1), 1000, snap_id_empresa=1, snap_id_sucursal=1),
    ]

    resultado = enriquecer_historial(crudo)

    mas_reciente = next(r for r in resultado if r.fecha == date(2026, 2, 1))
    assert mas_reciente.cambio_sucursal_vs_anterior is True
    assert mas_reciente.cambio_empresa_vs_anterior is False


def test_orden_de_salida_es_desc_igual_que_la_entrada() -> None:
    crudo = [_lectura(date(2026, 3, 1), 2000), _lectura(date(2026, 1, 1), 1000)]

    resultado = enriquecer_historial(crudo)

    assert [r.fecha for r in resultado] == [date(2026, 3, 1), date(2026, 1, 1)]
