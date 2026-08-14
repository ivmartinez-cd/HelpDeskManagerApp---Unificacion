"""SQL del parque de equipos sin contador real reciente contra SiGesReadOnly.

Lógica validada con paridad exacta contra el reporte legacy
`sitesphp.cdsa.com.ar/laprida/Operaciones/EquiposSinContadorReal/RUN.php`
(2026-08-14: mismo TOP por meses serial por serial, mismas fechas, mismos
IM-1..3; ver `backend/scripts/explore_siges_contadores_reales.py`):

- "Toma real" = `ID_TipoToma NOT IN (8, 13, 14, 19)` (Contador Inicial,
  Contador Final, Estimado, Promedio Instalación). Si el equipo nunca tuvo
  una real, la referencia es su primera toma histórica (instalación).
- Universo = máquinas vigentes (`Maquina.Estado=0`) en estados operativos
  {1 Activa en Cliente, 3 Backup, 8 Backup Fijo, 200 Baja Solicitada,
  254 No Localizado} que siguen facturando (última toma de cualquier tipo
  dentro del mes) y llevan >= 1 mes sin real. Divergencia consciente con el
  legacy: nuestro universo da ~15% más filas (el legacy aplica algún filtro
  adicional no identificado y trunca a 500); se prefiere el universo más
  amplio antes que replicar un recorte que nadie sabe justificar.
- IM-n = impresiones (clases 10 Mono + 20 Color) entre las últimas tomas
  consecutivas, de la más reciente hacia atrás.
- Divergencia deliberada adicional (pedido del usuario, 2026-08-14): se
  excluyen los dispositivos `PrintBox %` (cajas de monitoreo, no impresoras),
  que el legacy sí lista. El resto del universo con tomas es todo rubro
  "Impresoras" (plotters/escáneres/Zebra incluidos, que sí facturan por
  contador) — verificado contra `ArtGen.Id_Rubro`/`Rubro`.
"""

EQUIPOS_SIN_REAL_SQL = """
WITH resumen AS (
  SELECT C.ID_Maquina,
         MAX(CASE WHEN C.ID_TipoToma NOT IN (8, 13, 14, 19)
                  THEN C.FechaTomaContador END) AS ultima_real,
         MAX(C.FechaTomaContador) AS ultima_toma,
         MIN(C.FechaTomaContador) AS primera_toma
  FROM dbo.Contadores C
  WHERE C.Estado = 0
  GROUP BY C.ID_Maquina
),
universo AS (
  SELECT M.ID_Maquina, M.Nro_Serie, M.ID_Articulo, M.ID_Propietario, M.ID_Empresa,
         M.ID_Sucursal, M.ID_Estado_Maquina, M.Observ,
         R.ultima_real, COALESCE(R.ultima_real, R.primera_toma) AS fecha_ref
  FROM dbo.Maquina M
  INNER JOIN resumen R ON R.ID_Maquina = M.ID_Maquina
  WHERE M.Estado = 0
    AND M.ID_Estado_Maquina IN (1, 3, 8, 200, 254)
    AND DATEDIFF(month, R.ultima_toma, GETDATE()) <= 1
    AND DATEDIFF(month, COALESCE(R.ultima_real, R.primera_toma), GETDATE()) >= 1
),
tomas AS (
  SELECT C.ID_Maquina, C.ID_ClaseContador, C.Contador,
         ROW_NUMBER() OVER (PARTITION BY C.ID_Maquina, C.ID_ClaseContador
                            ORDER BY C.FechaTomaContador DESC) AS rn
  FROM dbo.Contadores C
  INNER JOIN universo U ON U.ID_Maquina = C.ID_Maquina
  WHERE C.Estado = 0 AND C.ID_ClaseContador IN (10, 20)
),
im AS (
  SELECT a.ID_Maquina,
         SUM(CASE WHEN a.rn = 1 THEN a.Contador - b.Contador ELSE 0 END) AS im1,
         SUM(CASE WHEN a.rn = 2 THEN a.Contador - b.Contador ELSE 0 END) AS im2,
         SUM(CASE WHEN a.rn = 3 THEN a.Contador - b.Contador ELSE 0 END) AS im3
  FROM tomas a
  INNER JOIN tomas b ON b.ID_Maquina = a.ID_Maquina
    AND b.ID_ClaseContador = a.ID_ClaseContador AND b.rn = a.rn + 1
  WHERE a.rn <= 3
  GROUP BY a.ID_Maquina
)
SELECT U.ID_Maquina AS id_maquina, U.ID_Empresa AS id_empresa_cliente,
       U.Nro_Serie AS serie, AG.Descripcion AS modelo, T.Descripcion AS tecnologia,
       EP.Den_Comercial AS propiedad, E.Den_Comercial AS cliente,
       S.descripcion AS sucursal, EM.Descripcion AS estado_maquina,
       U.Observ AS observaciones, U.ultima_real, U.fecha_ref,
       DATEDIFF(day, U.fecha_ref, GETDATE()) AS dias_sin_real,
       DATEDIFF(month, U.fecha_ref, GETDATE()) AS meses_sin_real,
       COALESCE(I.im1, 0) AS im1, COALESCE(I.im2, 0) AS im2, COALESCE(I.im3, 0) AS im3
FROM universo U
INNER JOIN dbo.Articulo A ON A.Id_Articulo = U.ID_Articulo
INNER JOIN dbo.ArtGen AG ON AG.Id_ArtGen = A.Id_ArtGen
LEFT JOIN dbo.Tecnologia T ON T.Id = AG.Id_Tecnologia
LEFT JOIN dbo.Empresa EP ON EP.ID_Empresa = U.ID_Propietario
INNER JOIN dbo.Empresa E ON E.ID_Empresa = U.ID_Empresa
INNER JOIN dbo.Sucursal S ON S.Id_Sucursal = U.ID_Sucursal
INNER JOIN dbo.Estado_Maquina EM ON EM.Id = U.ID_Estado_Maquina
LEFT JOIN im I ON I.ID_Maquina = U.ID_Maquina
WHERE AG.Descripcion NOT LIKE 'PrintBox%'
ORDER BY meses_sin_real DESC, cliente, serie
"""
