"""Query de incidentes en estado 'Derivado' (ID_Estado_Incidente=200), tipos
Correctivo (101) y Guardia (108), para la pantalla 'Incidentes sin consultar'
de Servicio Técnico.

'Derivado' = el operador le asignó el incidente a un PST pero todavía no lo
consultó con el técnico — recién pasa a 'En Curso' (300) cuando lo consulta.
Mismo catálogo Estado_Incidente que usan pendientes_query.py (500) y
mesa_ayuda_query.py (NOT IN 600/700/710/900); ver docs/siges/
SIGES_READONLY_CATALOGO_DATOS.md.

Que el incidente esté HOY en estado Derivado no alcanza para decidir solo:
importa si hubo una consulta ('En Curso', 300) DESPUÉS de la última vez que
entró en Derivado, no si tuvo una consulta alguna vez en toda su historia.
Caso real (incidente 846012, reportado 2026-09-12): Pendiente→Derivado→En
Curso→En Espera de Repuestos (ER)→Derivado de nuevo — al volver de ER queda
una consulta nueva pendiente aunque ya haya tenido una visita antes; con el
criterio viejo (cualquier estado fuera de 110/200 en toda la historia
descarta el incidente) este caso desaparecía de la pantalla sin que nadie lo
haya consultado. Confirmado con Iván que la regla es por la ÚLTIMA
derivación, no por el historial completo.

El historial de cambios de estado vive en `dbo.Instancia` (una fila por
transición, `ID_Instancia` autoincremental en orden de inserción,
`ID_Estado_Instancia` usa el mismo catálogo Estado_Incidente; columna
`Estado` es un flag propio de la fila, no el estado del incidente —
confirmado con scripts/explore_siges_instancia.py). Se usa `ID_Instancia`
para ordenar transiciones, no `Fecha`: en el caso real 846012 dos filas
consecutivas (En Espera de Repuestos y el Derivado siguiente) comparten el
mismo `Fecha` exacto, así que `Fecha` no alcanza para saber cuál fue
posterior. El `NOT EXISTS` excluye el incidente solo si existe una fila
En Curso (300) con `ID_Instancia` mayor al de la última fila Derivado (200)
de ese incidente — es decir, si ya hubo consulta para la derivación vigente.

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
    SELECT 1 FROM dbo.Instancia INS_CURSO
    WHERE INS_CURSO.ID_Incidente = I.ID_Incidente
    AND INS_CURSO.ID_Estado_Instancia = 300
    AND INS_CURSO.ID_Instancia > (
        SELECT MAX(INS_DER.ID_Instancia)
        FROM dbo.Instancia INS_DER
        WHERE INS_DER.ID_Incidente = I.ID_Incidente
        AND INS_DER.ID_Estado_Instancia = 200
    )
)
ORDER BY I.Fecha_Ingreso ASC
"""
