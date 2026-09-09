from src.modules.contadores.application.dtos.boxplot_parque_dto import BoxplotParqueDto
from src.modules.contadores.application.dtos.candidato_lectura_dto import CandidatoLecturaDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.application.dtos.solicitud_recalculo_siges_dto import (
    SolicitudRecalculoSigesDto,
)
from src.modules.contadores.application.use_cases._boxplot_de_entrada import boxplot_de_entrada
from src.modules.contadores.application.use_cases._construir_entrada_siges import (
    ConstructorEntradaSiges,
)
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    CandidatosEquipoPort,
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from src.modules.contadores.domain.ports.grilla_estimacion_port import GrillaEstimacionPort
from src.modules.contadores.domain.ports.recesos_port import RecesosPort
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia


class GetCandidatosEquipoSigesUseCase:
    """Variante real del panel de candidatos (MODELO_DE_DATOS.md §3.6): a
    diferencia del modo ejemplo (`get_candidatos_equipo.py`, que solo conoce
    los 4 puntos ya elegidos por el motor), acá se muestran las 24 lecturas
    reales tal cual están en Siges, para que el operador elija a mano.
    `grilla_gateway`/`recesos_store` son opcionales, mismo patrón que
    `RecalcularCandidatoSigesUseCase`: sin ellos (o sin `solicitud`, que
    identifica qué grilla cacheada reusar — ver `ConstructorEntradaSiges`)
    el equipo real se muestra igual, solo sin el gráfico de parque."""

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
        metadata = await self._port.fetch_metadata_equipo(id_maquina)
        if metadata is None:
            return None
        lecturas = await self._port.fetch_lecturas(id_maquina, id_clase_contador)
        boxplot = await self._boxplot(id_maquina, id_clase_contador, solicitud)
        return _dto_de(id_maquina, metadata, lecturas, boxplot)

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
        tecnologia=_tecnologia_de(metadata.id_tecnologia),
        velocidad_ppm=metadata.velocidad,
        lecturas=[_lectura_dto(lectura) for lectura in lecturas],
        boxplot=boxplot,
    )


def _lectura_dto(lectura: LecturaCandidataSiges) -> CandidatoLecturaDto:
    return CandidatoLecturaDto(
        fecha=lectura.fecha,
        tipo_toma=lectura.tipo_toma,
        valor=lectura.valor,
        valido=lectura.para_facturar,
        motivo_invalidez=None if lectura.para_facturar else "PF=0 (Servicio Técnico sin revisar)",
    )


def _tecnologia_de(id_tecnologia: int) -> Tecnologia:
    return "COLOR" if id_tecnologia == 2 else "MONO"
