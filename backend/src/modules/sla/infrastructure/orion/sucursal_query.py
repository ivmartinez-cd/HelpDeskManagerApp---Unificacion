"""Fragmentos `OUTER APPLY` que cruzan casos de Mesa de Ayuda con visitas de
técnico en la MISMA sucursal (`Incidente.ID_Sucursal`). Se componen dentro de
las queries de MDA y de derivados, que ya tienen el alias `I` del incidente.

"Visita de técnico" = caso con técnico asignado que no es MDA, ya derivado y
sin terminar: se excluyen 100 Condicional y 110 Pendiente (todavía sin
técnico), 500 Finalizado (el técnico ya fue; además hay finalizados zombis de
años) y los cerrados/anulados. Confirmado con Iván (2026-09-30): la alerta
cuenta cualquier técnico, no solo PST del interior, y aplica SOLO a
Correctivos (101) de los dos lados — el caso de MDA y la visita. Los demás
tipos (preventivos en lote, instalaciones, guardias) quedan afuera.

`COUNT(*) OVER ()` se evalúa antes del `TOP 1`: da el total de visitas de la
sucursal aunque solo se devuelva la más reciente."""

VISITA_EN_SUCURSAL_APPLY = """
OUTER APPLY (
    SELECT TOP 1
    V.ID_Incidente AS VisitaId,
    ET.Den_Comercial AS VisitaTecnico,
    EV.Descripcion AS VisitaEstado,
    COUNT(*) OVER () AS VisitaCantidad
    FROM dbo.Incidente V
    INNER JOIN dbo.Estado_Incidente EV ON V.ID_Estado_Incidente = EV.Id
    INNER JOIN dbo.Empresa ET ON V.ID_Tecnico = ET.ID_Empresa
    WHERE V.ID_Sucursal = I.ID_Sucursal
    AND V.ID_Tecnico <> I.ID_Tecnico
    AND V.ID_Tipo_Incidente = 101
    AND I.ID_Tipo_Incidente = 101
    AND V.ID_Estado_Incidente NOT IN (100, 110, 500, 600, 700, 710, 900)
    ORDER BY V.Fecha_Ingreso DESC
) VIS
"""

# Primer parámetro `?` de la query que lo incluya: el ID de MDA.
CASO_MDA_EN_SUCURSAL_APPLY = """
OUTER APPLY (
    SELECT TOP 1
    MDA.ID_Incidente AS MdaId,
    COUNT(*) OVER () AS MdaCantidad
    FROM dbo.Incidente MDA
    WHERE MDA.ID_Sucursal = I.ID_Sucursal
    AND MDA.ID_Incidente <> I.ID_Incidente
    AND MDA.ID_Tecnico = ?
    AND MDA.ID_Tipo_Incidente = 101
    AND I.ID_Tipo_Incidente = 101
    AND MDA.ID_Estado_Incidente NOT IN (600, 700, 710, 900)
    ORDER BY MDA.Fecha_Ingreso DESC
) CMDA
"""
