"""SQL para reconstruir el CSV de "Detalle de contadores por nro de proceso"
(reporte legacy SSRS `reportes.cdsa.com.ar:8090`) directo contra SiGesReadOnly,
sin pasar por la exportación manual — de cara a Estimación en 0.

Investigación documentada en
`backend/scripts/explore_siges_detalle_contadores_proceso.py` (reconstruida
contra datos reales; el RDL del reporte no es accesible desde acá — 401):

- El reporte sale de `dbo.Factura_Contador` (una fila por máquina + clase de
  contador dentro de un `Nro_Proceso`), joineado con `dbo.Maquina` (serie) y
  `dbo.Empresa` (cliente). Verificado 1:1 contra el proceso 99070 real
  (`ID_Maquina=20310` → `Nro_Serie=07QWB9UG3A004KV`).
- `ImpreContadorAnterior` es literalmente la columna `CONTADOR` que ya lee
  `CsvFaltaContadorReader` del CSV manual — no es casualidad, es la misma
  fuente de datos.
- "Falta Contador" = `ID_ContadorActual = ID_ContadorAnterior`: no se
  registró ninguna toma nueva en `dbo.Contadores` para esa máquina/clase este
  período (el FK "actual" reapunta a la última toma conocida). Distinto de
  `ImpresionesReales = 0` a secas, que también da positivo con una toma real
  de delta 0 (esos el reporte los marca "Automatico", no "Falta Contador").
  Verificado contra 41 filas reales del proceso 99070 (9 con falta) y 49 del
  99068 (18 con falta).
- Un `Nro_Proceso` cae en una sola `Empresa` y un solo `Anexo` (verificado en
  los 15 procesos más recientes) — el cliente sale sin ambigüedad de
  cualquier fila que exista para el proceso, tenga o no falta de contador.
"""

CLIENTE_POR_PROCESO_SQL = """
SELECT TOP 1 E.Den_Comercial AS cliente
FROM dbo.Factura_Contador FC
INNER JOIN dbo.Empresa E ON E.ID_Empresa = FC.ID_Empresa
WHERE FC.Nro_Proceso = ?
"""

FALTA_CONTADOR_POR_PROCESO_SQL = """
SELECT M.Nro_Serie AS serie, FC.ID_ClaseContador AS clase, FC.ImpreContadorAnterior AS contador
FROM dbo.Factura_Contador FC
INNER JOIN dbo.Maquina M ON M.ID_Maquina = FC.ID_Maquina
WHERE FC.Nro_Proceso = ?
  AND FC.ID_ContadorActual = FC.ID_ContadorAnterior
  AND FC.ID_ClaseContador IN (10, 20)
ORDER BY M.Nro_Serie, FC.ID_ClaseContador
"""
