from dataclasses import dataclass

from src.modules.contadores.domain.value_objects.estimacion.estado_maquina import Tecnologia

_VELOCIDAD_DEFAULT_PPM: dict[Tecnologia, float] = {"MONO": 45.0, "COLOR": 25.0}
_HORAS_JORNADA = 8


@dataclass(frozen=True, slots=True)
class PerfilEquipo:
    tecnologia: Tecnologia
    velocidad_ppm: float | None


def velocidad_efectiva(perfil: PerfilEquipo) -> float:
    """Si la velocidad no está cargada (None/0) o está mal cargada (1, error
    de carga común) se asume el default por tecnología en vez del dato
    crudo — un valor "1" da un techo absurdamente bajo y dispara falsos
    positivos (REGLAS_DE_NEGOCIO §7.1)."""
    if perfil.velocidad_ppm is None or perfil.velocidad_ppm <= 1:
        return _VELOCIDAD_DEFAULT_PPM[perfil.tecnologia]
    return perfil.velocidad_ppm


def hay_salto_imposible(
    impresiones_estimadas: float, dias_periodo: int, perfil: PerfilEquipo
) -> bool:
    """Detecta una estimación físicamente inviable para la velocidad del
    equipo (REGLAS_DE_NEGOCIO §7.1). Solo se evalúa con impresiones
    positivas — un ajuste hacia abajo nunca es un salto imposible."""
    if impresiones_estimadas <= 0 or dias_periodo <= 0:
        return False
    promedio_diario_implicito = impresiones_estimadas / dias_periodo
    techo_fisico = velocidad_efectiva(perfil) * 60 * _HORAS_JORNADA
    return promedio_diario_implicito > techo_fisico
