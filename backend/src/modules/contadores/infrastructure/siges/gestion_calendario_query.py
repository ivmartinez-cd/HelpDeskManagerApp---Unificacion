"""SQL de los eventos de facturación del calendario de planificación, leídos
directo de la base de la app de Gestión (`Gestion`, en el mismo SQL Server
ORION que Siges y con la misma cuenta de solo lectura) — ver ADR-047.

Replica lo que mostraba `GET /planificacion/ajax-by-rango` de la web,
validado el 2026-10-09 contra 828 eventos de la ventana ±90 días (0
faltantes, 0 sobrantes):

- `tipo_evento = 'F'` es facturación (`L`/`I`/`T`/`E`/`V` son otros tipos).
- Gestión tiene filas duplicadas por padre y fecha (la web las mandaba como
  un solo evento con lista de ids): se agrupa por `evento_padre_id` (o el
  propio id si no tiene padre) + día, se toma el de menor id y el grupo se
  muestra solo si ESE evento no está realizado.
- El operador es `Gestion.dbo.usuario` (NO `SiGes.dbo.UsuariosWeb`: los ids
  no coinciden). Rango con placeholders: desde inclusive, hasta exclusivo."""

GESTION_CALENDARIO_FACTURACION_SQL = """
WITH ev AS (
  SELECT ce.id, ce.fecha, ce.titulo, ce.descripcion, ce.realizado,
         u.username, u.color_calendario_planificacion AS color,
         ROW_NUMBER() OVER (
           PARTITION BY COALESCE(ce.evento_padre_id, -ce.id), CAST(ce.fecha AS date)
           ORDER BY ce.id
         ) AS orden
  FROM Gestion.dbo.calendario_evento ce
  LEFT JOIN Gestion.dbo.usuario u ON u.id = ce.usuario_operador_facturacion_id
  WHERE ce.tipo_evento = 'F' AND ce.fecha >= ? AND ce.fecha < ?
)
SELECT id, fecha, titulo, CAST(descripcion AS nvarchar(max)) AS descripcion, username, color
FROM ev
WHERE orden = 1 AND ISNULL(realizado, 0) = 0
ORDER BY fecha, id
"""
