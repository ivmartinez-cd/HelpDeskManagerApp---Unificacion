from typing import Literal

# `FuenteEstimacion` del legacy más "Pendiente" (`RequierePendiente`). No hay
# "Backup con ST": un Backup con T4 válido sale como `T4_ST`.
FuenteEstimacion = Literal[
    "Sin_Estimar",
    "Historia_Propia",
    "T4_ST",
    "Backup_SinST",
    "EnTransito",
    "Parque_Cliente_Modelo",
    "Parque_Grupo_Modelo",
    "Parque_Cliente_Tec",
    "Parque_Global_Modelo",
    "Pendiente",
]

Semaforo = Literal["VERDE", "AMARILLO", "NARANJA", "ROJO"]
Coloreo = Literal["AZUL", "NARANJA", "NORMAL"]

# `MetodoEstimacion` del legacy (tooltip, auditoría y observación del CSV).
# "NoAplica" = fila sin `EstimacionDecision` (lectura real / pendiente).
MetodoEstimacion = Literal[
    "NoAplica",
    "MedianaTruncadaP80",
    "MedianaCruda",
    "EntreReales",
    "ContadorAnterior",
    "T4ST_Valor",
    "T4ST_Proyectado",
]

# `MarcasEstimacion` (flags) del legacy: circunstancias del cálculo que el
# resumen de la observación del CSV lee sin re-parsear `detalle_calculo`.
MarcaEstimacion = Literal[
    "AjustadoPorReceso",
    "UsaT4EnPar",
    "T4SinRevisar",
    "SinParValido",
    "InterpoladoAtras",
    "PLManual",
    "ForzadoPorOperador",
]
