"""Valores de `estado_maquina` que el universo "sin real" trata distinto del
resto (ver docstring de `equipos_sin_real_query`: el universo mezcla Activa en
Cliente, Backup, Backup Fijo, Baja Solicitada y No Localizado). Única fuente
de verdad de estos dos literales — no repetirlos sueltos en cada archivo que
los compara."""

ACTIVA_EN_CLIENTE = "Activa en Cliente"
NO_LOCALIZADO = "No Localizado"
