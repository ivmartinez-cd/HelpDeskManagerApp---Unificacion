from src.modules.contadores.application.dtos.candidato_lectura_dto import CandidatoLecturaDto
from src.modules.contadores.application.dtos.candidatos_equipo_dto import CandidatosEquipoDto
from src.modules.contadores.domain.ports.candidatos_equipo_port import (
    CandidatosEquipoPort,
    LecturaCandidataSiges,
    MetadataEquipoSiges,
)
from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia


class GetCandidatosEquipoSigesUseCase:
    """Variante real del panel de candidatos (MODELO_DE_DATOS.md §3.6): a
    diferencia del modo ejemplo (`get_candidatos_equipo.py`, que solo conoce
    los 4 puntos ya elegidos por el motor), acá se muestran las 24 lecturas
    reales tal cual están en Siges, para que el operador elija a mano.
    `boxplot=None` siempre — no hay muestra cruda de parque en este
    endpoint (si hiciera falta, se calcularía en la grilla, no acá)."""

    def __init__(self, port: CandidatosEquipoPort) -> None:
        self._port = port

    async def execute(self, id_maquina: int, id_clase_contador: int) -> CandidatosEquipoDto | None:
        metadata = await self._port.fetch_metadata_equipo(id_maquina)
        if metadata is None:
            return None
        lecturas = await self._port.fetch_lecturas(id_maquina, id_clase_contador)
        return _dto_de(id_maquina, metadata, lecturas)


def _dto_de(
    id_maquina: int, metadata: MetadataEquipoSiges, lecturas: list[LecturaCandidataSiges]
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
        boxplot=None,
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
