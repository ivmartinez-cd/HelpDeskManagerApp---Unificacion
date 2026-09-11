"""Consulta a Siges del detalle de incidentes de un técnico puntual — mismo
JOIN base y mismo mapeo `ID_Tipo_Incidente` -> categoría que
`query.py` (ver ese módulo, incluido el fix 2026-08-25 de `Fecha_Cierre` en
vez de `IncidenteTiempo.FechaOperativo`), filtrada por `E1.ID_Empresa` en vez
de agrupada por técnico: es la pantalla de detalle, uno a la vez."""

INCIDENTES_TECNICO_SQL = """
SELECT
    I.ID_Incidente AS IdIncidente,
    CASE I.ID_Tipo_Incidente
        WHEN 101 THEN 'Correctivo'
        WHEN 102 THEN 'Preventivo'
        WHEN 103 THEN 'InstDes'
        WHEN 107 THEN 'PreCorrectivo'
        WHEN 204 THEN 'EntregaInsumos'
    END AS Categoria,
    E.Den_Comercial AS Cliente,
    S.Descripcion AS Sucursal,
    M.Nro_Serie AS NroSerie
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
AND E1.ID_Empresa = ?
AND I.Fecha_Cierre BETWEEN ? AND ?
AND YEAR(I.Fecha_Cierre)*100+MONTH(I.Fecha_Cierre) = ?
ORDER BY
    CASE I.ID_Tipo_Incidente
        WHEN 101 THEN 1
        WHEN 102 THEN 2
        WHEN 103 THEN 3
        WHEN 107 THEN 4
        WHEN 204 THEN 5
    END,
    I.ID_Incidente DESC
"""
