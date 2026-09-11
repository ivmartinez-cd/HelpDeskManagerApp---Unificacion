"""Query de incidentes en estado 'Derivado' (ID_Estado_Incidente=200), tipos
Correctivo (101) y Guardia (108), para la pantalla 'Incidentes sin consultar'
de Servicio Técnico.

'Derivado' = el operador le asignó el incidente a un PST pero todavía no lo
consultó con el técnico — recién pasa a 'En Curso' (300) cuando lo consulta.
Mismo catálogo Estado_Incidente que usan pendientes_query.py (500) y
mesa_ayuda_query.py (NOT IN 600/700/710/900); ver docs/siges/
SIGES_READONLY_CATALOGO_DATOS.md.

Que el incidente esté HOY en estado Derivado no alcanza: un caso puede haber
pasado por 'En Curso' (300) o cualquier otro estado intermedio (ej. 'En
Espera de Repuestos') y haber vuelto a Derivado después — ahí sí hubo una
visita previa, no es "sin consultar". El historial completo de cambios de
estado vive en `dbo.Instancia` (una fila por transición, `ID_Estado_Instancia`
usa el mismo catálogo Estado_Incidente; columna `Estado` es un flag propio de
la fila, no el estado del incidente — confirmado con
scripts/explore_siges_instancia.py contra el incidente real 842550: 5
instancias, Pendiente→Derivado→En Curso→En Espera de Repuestos→Derivado).
El `NOT EXISTS` exige que la ÚNICA transición registrada haya sido
Pendiente (110) → Derivado (200) — cualquier otro estado en el historial
(incluida una re-derivación sin haber pasado por 300) descarta el incidente.

Sin JOIN a `dbo.IncidenteTiempo`: un incidente Derivado no está finalizado,
no tiene fila ahí (mismo razonamiento que mesa_ayuda_query.py).

El rango de fechas (`desde`/`hasta`, inclusive) lo deriva el caso de uso del
período mensual AAAAMM elegido en la pantalla — no hay corte histórico fijo
acá, se navega mes a mes.

SQL 100% parametrizado con `?`, sin interpolación (ARCHITECTURE_GUIDE §8)."""

INCIDENTES_DERIVADOS_SQL = """
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
DATEDIFF(day, I.Fecha_Ingreso, GETDATE()) AS DiasDesdeIngreso
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
INNER JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
INNER JOIN dbo.Maquina M ON I.ID_Maquina = M.ID_Maquina
INNER JOIN dbo.Articulo A ON M.ID_Articulo = A.Id_Articulo
INNER JOIN dbo.ArtGen AG ON A.Id_ArtGen = AG.Id_ArtGen
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = I.ID_Sucursal
INNER JOIN dbo.Empresa E ON I.ID_Empresa = E.ID_Empresa
INNER JOIN dbo.Empresa E1 ON I.ID_Tecnico = E1.ID_Empresa
WHERE I.ID_Tipo_Incidente IN (101, 108)
AND I.ID_Estado_Incidente = 200
AND I.Fecha_Ingreso >= ?
AND I.Fecha_Ingreso < DATEADD(day, 1, ?)
AND NOT EXISTS (
    SELECT 1 FROM dbo.Instancia INS
    WHERE INS.ID_Incidente = I.ID_Incidente
    AND INS.ID_Estado_Instancia NOT IN (110, 200)
)
ORDER BY I.Fecha_Ingreso ASC
"""
