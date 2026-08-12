[ROL]
Sos un Arquitecto y Desarrollador Full-Stack Senior especializado en FastAPI (Python 3.12), SQL Server (pyodbc), Clean Architecture y React / Next.js con TypeScript. Respondés en español de Argentina con voseo natural, directo y sin texto de relleno.

[CONTEXTO]
El sistema HelpDeskManager-Unificacion requiere incorporar en la pantalla de inicio (Dashboard principal) la información de cumplimiento de SLAs e incidentes vencidos extraídos directamente de la base de datos SQL Server `MERCURIO` (base `Siges`).

Actualmente este control se realiza manualmente mediante una tabla dinámica de Excel donde se filtran los incidentes por rango de fechas (Desde/Hasta) y Período (AAAAMM). La planilla muestra:
1. El porcentaje y total de incidentes "Correcto" vs "Vencido" (ej: 412 Correctos [94,90%] vs 21 Vencidos [5,10%]).
2. El desglose detallado de los incidentes VENCIDOS agrupados por Técnico / PST (ej: CD - Nicolás MON, PST Comodoro Rivadavia, etc.) con sus respectivos IDs de incidente.

La consulta SQL exacta que se debe ejecutar contra la BD es la siguiente:

```sql
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
CASE WHEN LEFT(E1.Den_Comercial,2) = 'CD'  THEN 'LOCAL' ELSE 'INTERIOR' END AS REGION,
IT.FechaOperativo,
YEAR(IT.FechaOperativo)*100+MONTH(IT.FechaOperativo) AS Periodo,
IT.Tiempo,
CASE WHEN CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) BETWEEN 0 AND 23 THEN '0 a 24' WHEN CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) BETWEEN 24 AND 47 THEN '24 a 48' WHEN CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) BETWEEN 48 AND 71 THEN '48 a 72' WHEN CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) BETWEEN 72 AND 95 THEN '72 a 96' ELSE '96hs o mas' END AS RANGO,
I.SLA,
CASE WHEN CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) <= I.SLA THEN '0' ELSE CAST((CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) - I.SLA) AS VARCHAR) END AS HorasVencido,
CASE WHEN CAST(SUBSTRING(IT.Tiempo, 1, CHARINDEX(':', IT.Tiempo) - 1) AS INT) < I.SLA THEN 'Correcto' ELSE 'Vencido' END AS Resultado,
IT.Reloj,
CAST(IT.Descuento AS DECIMAL(10,2)) AS DemoraTotal,
CAST(IT.DescuentoDemora AS DECIMAL(10,2)) AS DesDemora,
IT.DescuentoOperaFeriados,
IT.DescuentoOPFS
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
WHERE I.ID_Tipo_Incidente IN (101, 108)
AND IT.FechaOperativo BETWEEN ? AND ?
AND YEAR(IT.FechaOperativo)*100+MONTH(IT.FechaOperativo) = ?
ORDER BY I.ID_Incidente DESC
