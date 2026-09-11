"""Query de incidentes en estado 'Finalizado' (ID_Estado_Incidente=500),
tipos Correctivo (101), Preventivo (102) e Instalación-Desinstalación (103),
para la pantalla 'Pendientes a Cerrar' de Servicio Técnico.

Definición operativa confirmada con dato real 2026-08-14 mediante
explore_siges_incidentes_sin_cerrar.py:
  - Estado 500 = 'Finalizado': el técnico completó el servicio, falta cierre
    formal en Gestión. En 24 meses hay 232 en ese estado — todos con fila en
    IncidenteTiempo (sin_tiempo=0), por lo que el INNER JOIN es seguro.
  - El corte temporal (? meses) limita el backlog histórico para acotar costo;
    configurado por PENDIENTES_MESES_CORTE (default 24).

Filtro de tipos corregido 2026-08-25: el original heredaba IN (101, 108) del
módulo de cumplimiento SLA (query.py), pero 108 es 'Guardia', no una de las
planillas que Servicio Técnico cierra acá (ver docs/siges/
SIGES_READONLY_CATALOGO_DATOS.md). "Pendientes a Cerrar" es un criterio propio
e independiente del de cumplimiento SLA, que sigue usando (101, 108).

SQL 100% parametrizado con `?`, sin interpolación (ARCHITECTURE_GUIDE §8).
El placeholder de `meses_corte` va como argumento de DATEADD — pyodbc lo
pasa como INT y SQL Server lo acepta en esa posición."""

INCIDENTES_SIN_CERRAR_SQL = """
SELECT
I.ID_Incidente,
I.Fecha_Ingreso,
TI.Descripcion AS Tipo,
EI.Descripcion AS Estado,
E.Den_Comercial,
S.Descripcion AS Sucursal,
M.Nro_Serie,
AG.Descripcion AS Modelo,
E1.Den_Comercial AS Tecnico,
E1.ID_Empresa AS IdTecnico,
IT.FechaOperativo,
DATEDIFF(day, IT.FechaOperativo, GETDATE()) AS DiasEnEstado
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
INNER JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
INNER JOIN dbo.Maquina M ON I.ID_Maquina = M.ID_Maquina
INNER JOIN dbo.Articulo A ON M.ID_Articulo = A.Id_Articulo
INNER JOIN dbo.ArtGen AG ON A.Id_ArtGen = AG.Id_ArtGen
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = I.ID_Sucursal
INNER JOIN dbo.Empresa E ON I.ID_Empresa = E.ID_Empresa
INNER JOIN dbo.Empresa E1 ON I.ID_Tecnico = E1.ID_Empresa
INNER JOIN dbo.IncidenteTiempo IT ON IT.ID_Incidente = I.ID_Incidente
WHERE I.ID_Tipo_Incidente IN (101, 102, 103)
AND I.ID_Estado_Incidente = 500
AND I.Fecha_Ingreso >= DATEADD(MONTH, -?, GETDATE())
ORDER BY IT.FechaOperativo ASC
"""
