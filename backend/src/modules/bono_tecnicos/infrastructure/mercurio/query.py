"""Consulta agrupada a Siges para el bono de técnicos — reemplaza las 5
conexiones ODBC (una por categoría) que "Tecnicos.xlsx" refrescaba a mano, una
vez por técnico, para armar `Lista!I1:J9`. Mismo JOIN base que la consulta
legacy de SLA/preventivos (ARCHITECTURE_GUIDE §8: placeholders, nada se
interpola); no sacar ningún INNER JOIN aunque no aporte columnas al SELECT —
achicar el JOIN puede cambiar qué filas matchean y correr el conteo.

Mapeo `ID_Tipo_Incidente` -> categoría, tal como estaba cableado en las 5
conexiones ODBC del Excel (`Lista!I1:I5`): 101=Correctivo, 102=Preventivo,
103=Instalación-Desinstalación, 107=Pre-Correctivo, 204=Entrega de Insumos.
Filtro `LEFT(E1.Den_Comercial,2) = 'CD'`: solo técnicos de planta (Canal
Directo), no prestadores externos — esos tienen su propio módulo
(liquidaciones/prestadores).

Filtro de período por `I.Fecha_Cierre`, no por `IncidenteTiempo.FechaOperativo`
(bug real encontrado y corregido 2026-08-25): `FechaOperativo` es el campo de
timing de SLA, no el mes en que se paga el bono. Verificado contra el pago real
de julio/2026 a Agustín Haczek (el gerente comparte por fuera del sistema una
fila con esos números) — con `FechaOperativo` el total de Correctivo+InstDes+
EntregaInsumos daba 99 y el puntaje 7.07; con `Fecha_Cierre` da 100 y 7.12,
calzando exacto. El JOIN a `IncidenteTiempo` se sacó a propósito (no aportaba
ninguna columna al SELECT, solo el filtro de fecha equivocado)."""

CONTEOS_TECNICOS_SQL = """
SELECT
    E1.Den_Comercial AS Tecnico,
    E1.ID_Empresa AS IdTecnico,
    CASE I.ID_Tipo_Incidente
        WHEN 101 THEN 'Correctivo'
        WHEN 102 THEN 'Preventivo'
        WHEN 103 THEN 'InstDes'
        WHEN 107 THEN 'PreCorrectivo'
        WHEN 204 THEN 'EntregaInsumos'
    END AS Categoria,
    COUNT(*) AS Cantidad
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
INNER JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
INNER JOIN dbo.Maquina M ON I.ID_Maquina = M.ID_Maquina
INNER JOIN dbo.Articulo A ON M.ID_Articulo = A.Id_Articulo
INNER JOIN dbo.ArtGen AG ON A.Id_ArtGen = AG.Id_ArtGen
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = I.ID_Sucursal
INNER JOIN dbo.Empresa E ON I.ID_Empresa = E.ID_Empresa
INNER JOIN dbo.Empresa E1 ON I.ID_Tecnico = E1.ID_Empresa
WHERE I.ID_Tipo_Incidente IN (101, 102, 103, 107, 204)
AND LEFT(E1.Den_Comercial, 2) = 'CD'
AND I.Fecha_Cierre BETWEEN ? AND ?
AND YEAR(I.Fecha_Cierre)*100+MONTH(I.Fecha_Cierre) = ?
GROUP BY E1.Den_Comercial, E1.ID_Empresa, I.ID_Tipo_Incidente
ORDER BY E1.Den_Comercial
"""
