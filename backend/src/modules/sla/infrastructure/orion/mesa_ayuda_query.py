"""Query de incidentes sin cerrar asignados al técnico 'CD - Mesa de Ayuda'
(`dbo.Empresa.ID_Empresa`, configurado en `settings.mesa_ayuda_siges_empresa_id`,
default 428 — confirmado contra Siges 2026-08-25).

'Sin cerrar' = todo estado salvo Cerrado (600), Resuelto (700), Resuelto
c/pendientes (710) y Anulado (900) — a diferencia de `pendientes_query.py`
(que filtra a estado 500 Finalizado, tipos 101/108), acá no hay corte por
tipo ni por estado 500: ninguno de los incidentes de MDA pasa nunca por ese
estado, así que esa query siempre da cero filas para este técnico.

Sin JOIN a `dbo.IncidenteTiempo`: esos incidentes no están finalizados, no
tienen fila ahí. `LEFT JOIN` a `dbo.UsuariosWeb` resuelve el nombre real del
último operador que tocó el incidente (`Usuario_Mod`) sin perder la fila si
el login no está en el catálogo.

Verificado contra datos reales (2026-08-25): 43 filas sin cerrar para
ID_Empresa=428, mismo conteo con los INNER JOIN de Maquina/Articulo/ArtGen/
Sucursal/Empresa que con el `Incidente` solo — no pierden filas.

SQL 100% parametrizado con `?`, sin interpolación (ARCHITECTURE_GUIDE §8)."""

INCIDENTES_MESA_AYUDA_SQL = """
SELECT
I.ID_Incidente,
I.Fecha_Ingreso,
TI.Descripcion AS Tipo,
EI.Descripcion AS Estado,
E.Den_Comercial,
S.Descripcion AS Sucursal,
M.Nro_Serie,
AG.Descripcion AS Modelo,
I.Usuario_Mod AS OperadorLogin,
UW.nombre AS OperadorNombre,
UW.apellido AS OperadorApellido,
DATEDIFF(day, I.Fecha_Ingreso, GETDATE()) AS DiasTranscurridos
FROM dbo.Incidente I
INNER JOIN dbo.Estado_Incidente EI ON I.ID_Estado_Incidente = EI.Id
INNER JOIN dbo.Tipo_Incidente TI ON I.ID_Tipo_Incidente = TI.Id
INNER JOIN dbo.Maquina M ON I.ID_Maquina = M.ID_Maquina
INNER JOIN dbo.Articulo A ON M.ID_Articulo = A.Id_Articulo
INNER JOIN dbo.ArtGen AG ON A.Id_ArtGen = AG.Id_ArtGen
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = I.ID_Sucursal
INNER JOIN dbo.Empresa E ON I.ID_Empresa = E.ID_Empresa
LEFT JOIN dbo.UsuariosWeb UW ON UW.login = I.Usuario_Mod
WHERE I.ID_Tecnico = ?
AND I.ID_Estado_Incidente NOT IN (600, 700, 710, 900)
ORDER BY I.Fecha_Ingreso ASC
"""
