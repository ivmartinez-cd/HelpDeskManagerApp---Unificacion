from typing import Literal

FuenteEstimacion = Literal[
    "Sin_Estimar",
    "Historia_Propia",
    "T4_ST",
    "Backup_SinST",
    "Backup_ConST",
    "EnTransito",
    "Parque_Cliente_Modelo",
    "Parque_Grupo_Modelo",
    "Parque_Cliente_Tec",
    "Parque_Global_Modelo",
    "Pendiente",
]

Semaforo = Literal["VERDE", "AMARILLO", "NARANJA", "ROJO"]
Coloreo = Literal["AZUL", "NARANJA", "NORMAL"]
