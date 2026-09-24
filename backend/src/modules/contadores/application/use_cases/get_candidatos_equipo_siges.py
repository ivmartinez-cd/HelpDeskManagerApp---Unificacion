from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.application.dtos.candidato_lectura_dto import CandidatoLecturaDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.fila_grilla_siges_dto import FilaGrillaSigesDto
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases._boxplot_de_entrada import boxplot_de_entrada
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.application.use_cases._mapear_filas_grilla_siges import (
    tecnologia_de,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    CandidatosEquipoPort,
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort

_ETIQUETA_OK = "✓ ok"


class GetCandidatosEquipoSigesUseCase:
    """Variante real del panel de candidatos (MODELO_DE_DATOS.md §3.6): a
    diferencia del modo ejemplo (`get_candidatos_equipo.py`, que solo conoce
    los 4 puntos ya elegidos por el motor), acá se muestran las 24 lecturas
    reales tal cual están en Siges (con su etiqueta de validación, si sirven
    como P/L y las marcas de cambio de empresa/sucursal/anexo del legacy),
    para que el operador elija a mano.
    `grilla_gateway`/`recesos_store` son opcionales. Con ellos y con `solicitud` (que
    identifica qué grilla ya cargada reusar — ver `ConstructorEntradaSiges`)
    la cabecera sale de la fila de la grilla, como `PanelCandidatos` del
    legacy (`Equipo.Raw`: empresa/sucursal/sector del SNAPSHOT del proceso,
    lo que se factura). Sin ellos, o si el equipo no está en esa grilla, se
    usa la ubicación actual de la máquina y no hay gráfico de parque."""

    def __init__(
        self,
        port: CandidatosEquipoPort,
        grilla_gateway: GrillaEstimacionPort | None = None,
        recesos_store: RecesosPort | None = None,
    ) -> None:
        self._port = port
        self._constructor_entrada = (
            ConstructorEntradaSiges(grilla_gateway, recesos_store)
            if grilla_gateway is not None and recesos_store is not None
            else None
        )

    async def execute(
        self,
        id_maquina: int,
        id_clase_contador: int,
        solicitud: SolicitudRecalculoSigesDto | None = None,
    ) -> CandidatosEquipoDto | None:
        metadata = await self._metadata(id_maquina, id_clase_contador, solicitud)
        if metadata is None:
            return None
        lecturas = await self._port.fetch_lecturas(id_maquina, id_clase_contador)
        boxplot = await self._boxplot(id_maquina, id_clase_contador, solicitud)
        return _dto_de(id_maquina, metadata, lecturas, boxplot)

    async def _metadata(
        self, id_maquina: int, id_clase_contador: int, solicitud: SolicitudRecalculoSigesDto | None
    ) -> MetadataEquipoSiges | None:
        fila = None
        if self._constructor_entrada is not None and solicitud is not None:
            fila = await self._constructor_entrada.fila(
                id_maquina, str(id_clase_contador), solicitud
            )
        if fila is None:
            return await self._port.fetch_metadata_equipo(id_maquina)
        return _metadata_de_fila(fila)

    async def _boxplot(
        self, id_maquina: int, id_clase_contador: int, solicitud: SolicitudRecalculoSigesDto | None
    ) -> BoxplotParqueDto | None:
        if self._constructor_entrada is None or solicitud is None:
            return None
        resultado = await self._constructor_entrada.construir(
            id_maquina, str(id_clase_contador), solicitud
        )
        if resultado is None:
            return None
        entrada, _recesos = resultado
        return boxplot_de_entrada(entrada)


def _metadata_de_fila(fila: FilaGrillaSigesDto) -> MetadataEquipoSiges:
    return MetadataEquipoSiges(
        nro_serie=fila.nro_serie,
        empresa=fila.empresa_desc,
        sucursal=fila.sucursal_desc,
        sector=fila.sector_desc,
        modelo=fila.modelo_desc,
        id_tecnologia=fila.id_tecnologia,
        velocidad=fila.velocidad,
    )


def _dto_de(
    id_maquina: int,
    metadata: MetadataEquipoSiges,
    lecturas: list[LecturaCandidataSiges],
    boxplot: BoxplotParqueDto | None,
) -> CandidatosEquipoDto:
    return CandidatosEquipoDto(
        id_maquina=id_maquina,
        nro_serie=metadata.nro_serie,
        empresa=metadata.empresa,
        sucursal=metadata.sucursal,
        sector=metadata.sector or "",
        modelo=metadata.modelo,
        tecnologia=tecnologia_de(metadata.id_tecnologia),
        velocidad_ppm=metadata.velocidad,
        lecturas=[_lectura_dto(lectura) for lectura in lecturas],
        boxplot=boxplot,
    )


def _lectura_dto(lectura: LecturaCandidataSiges) -> CandidatoLecturaDto:
    etiqueta = lectura.etiqueta_validacion
    valido = etiqueta == _ETIQUETA_OK
    return CandidatoLecturaDto(
        fecha=lectura.fecha,
        tipo_toma=lectura.tipo_toma,
        valor=lectura.valor,
        valido=valido,
        motivo_invalidez=None if valido else etiqueta,
        id_contador=lectura.id_contador,
        desc_tipo_toma=lectura.desc_tipo_toma,
        para_facturar=lectura.para_facturar,
        usable=lectura.usable,
        etiqueta_validacion=etiqueta,
        cambio_empresa_vs_anterior=lectura.cambio_empresa_vs_anterior,
        cambio_sucursal_vs_anterior=lectura.cambio_sucursal_vs_anterior,
        cambio_anexo_vs_anterior=lectura.cambio_anexo_vs_anterior,
    )
