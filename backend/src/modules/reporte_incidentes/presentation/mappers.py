from dataclasses import asdict

from src.modules.reporte_incidentes.application.use_cases.vista_reporte import VistaReporte
from src.modules.reporte_incidentes.domain.services.resumen import Resumen
from src.modules.reporte_incidentes.domain.value_objects.periodo import etiqueta_rango
from src.modules.reporte_incidentes.presentation.schemas.reporte_schemas import (
    CategoriaSchema,
    ConteoSchema,
    ConteoSubcategoriaSchema,
    EmpresaSchema,
    FiltrosSchema,
    KpisSchema,
    OpcionesFiltroSchema,
    OportunidadesMejoraSchema,
    ReporteResponse,
)


def _kpis(resumen: Resumen) -> KpisSchema:
    campos = asdict(resumen)
    return KpisSchema.model_validate({k: campos[k] for k in KpisSchema.model_fields})


def _graficos(completo: Resumen) -> dict[str, object]:
    return {
        "categorias": [ConteoSchema.model_validate(c) for c in completo.categorias],
        "subcategorias": [
            ConteoSubcategoriaSchema.model_validate(s) for s in completo.subcategorias
        ],
        "sucursales": [ConteoSchema.model_validate(s) for s in completo.sucursales],
    }


def _encabezado(vista: VistaReporte) -> dict[str, object]:
    reporte = vista.reporte
    return {
        "empresa": EmpresaSchema.model_validate(reporte.empresa),
        "periodo": str(reporte.hasta),
        "meses": reporte.meses,
        "periodos": [str(p) for p in reporte.periodos],
        "rango_etiqueta": etiqueta_rango(reporte.hasta, reporte.meses),
        "generado_en": reporte.generado_en,
        "pendientes_ia": reporte.pendientes,
        "pendientes_revision": vista.pendientes_revision,
    }


def _taxonomia(vista: VistaReporte) -> list[CategoriaSchema]:
    return [
        CategoriaSchema(nombre=c.nombre, color=c.color, subcategorias=list(c.subcategorias))
        for c in vista.reporte.taxonomia
    ]


def a_respuesta(vista: VistaReporte) -> ReporteResponse:
    return ReporteResponse.model_validate({
        **_encabezado(vista),
        **_graficos(vista.completo),
        "filtros": FiltrosSchema.model_validate(vista.filtros),
        "filtros_activos": vista.filtros.activos,
        "opciones": OpcionesFiltroSchema.model_validate(vista.opciones),
        "kpis": _kpis(vista.seleccion),
        "evolucion": [ConteoSchema.model_validate(c) for c in vista.seleccion.evolucion],
        "oportunidades": OportunidadesMejoraSchema.model_validate(vista.oportunidades),
        "colores": vista.colores,
        "taxonomia": _taxonomia(vista),
    })
