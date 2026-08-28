"""SQL de anexos de Impresión pendientes de cierre contra SiGesReadOnly.

Recrea el reporte legacy `sitesphp/.../SiGes/AnexosNoFacturados/RUN.php`
acotado a lo que pidió la TL (2026-08-14): solo anexos de tipo Impresión
(la "opción Impresión" del formulario legacy) — todo lo FACTURADO / LIBERADO
/ A LIBERAR queda afuera. El mes en curso se incluye (desde 2026-08-28) para
que la UI pueda filtrarlo aparte como MES_EN_CURSO (ver
`periodos_facturacion.estado_de_periodo`); el parámetro de corte de período
pasó de excluyente a inclusive (`<=`). Semántica validada con dato real
contra el legacy
(`backend/scripts/explore_siges_anexos_no_facturados.py` y rondas 3-5):

- `Factura_Anexo` tiene una fila por (anexo, período de facturación); el
  proceso es secuencial por anexo, la última fila es el período abierto.
  Solo los anexos `discriminador='I'` facturan por acá (2999 anexos); los
  tipos C/D/G van por el flujo genérico, cuya única vista visible en la
  réplica (`factura_contrato_anexo_generico`) está rota (error 4502).
- "Pendiente" = `Facturado=0 AND ListoParaFacturar=0`. Con `Listo=1` el
  legacy muestra A LIBERAR; con `Facturado=1`, LIBERADO/FACTURADO.
- El legacy recorta con `ID_EstadoAnexo=1` (Activo) y una ventana de
  recencia sobre `Fecha_Proceso` (12 meses de la referencia): los
  pendientes zombis de 2014-2024 que nadie va a cerrar no aparecen.
  Verificado 1:1 contra las 43 filas tipo I del reporte del 2026-08-14.
- Importe "USD" del legacy = `SUM(Factura_SubProceso.ImporteTotalDolares)`
  del proceso pendiente (verificado exacto: 6.472,41 para SUMCDSI0077/C2).
- FECHA del legacy = `Factura_Anexo.Fecha_Proceso`.
"""

ANEXOS_PENDIENTES_SQL = """
WITH ultimo AS (
  SELECT FA.ID_Anexo, FA.PeriodoFacturacion, FA.Nro_Proceso, FA.Fecha_Proceso,
         FA.ListoParaFacturar, FA.Facturado,
         ROW_NUMBER() OVER (PARTITION BY FA.ID_Anexo
                            ORDER BY FA.PeriodoFacturacion DESC,
                                     FA.Nro_Proceso DESC) AS rn
  FROM dbo.Factura_Anexo FA
)
SELECT A.ID_Anexo AS id_anexo, A.NombreAnexo AS anexo,
       G.descripcion AS grupo, C.NombreContrato AS contrato,
       C.ID_EmpresaAdmin AS id_empresa_admin,
       EA.Den_Comercial AS empresa_admin, V.Descripcion AS vendedor,
       MO.Descripcion AS moneda, MF.Descripcion AS moneda_facturacion,
       u.PeriodoFacturacion AS periodo, u.Fecha_Proceso AS fecha_proceso,
       (SELECT COALESCE(SUM(FS.ImporteTotalDolares), 0)
        FROM dbo.Factura_SubProceso FS
        WHERE FS.Nro_Proceso = u.Nro_Proceso
          AND FS.ID_Anexo = u.ID_Anexo) AS importe_usd
FROM ultimo u
INNER JOIN dbo.Anexo A ON A.ID_Anexo = u.ID_Anexo
LEFT JOIN dbo.Contrato C ON C.ID_Contrato = A.ID_Contrato
LEFT JOIN dbo.GrupoEconomico G ON G.id = A.ID_GrupoE
LEFT JOIN dbo.Empresa EA ON EA.ID_Empresa = C.ID_EmpresaAdmin
LEFT JOIN dbo.Vendedor V ON V.Id_Vendedor = C.Id_Vendedor
LEFT JOIN dbo.Moneda MO ON MO.Id = A.moneda_id
LEFT JOIN dbo.Moneda MF ON MF.Id = A.moneda_facturacion_id
WHERE u.rn = 1
  AND u.Facturado = 0
  AND u.ListoParaFacturar = 0
  AND A.ID_EstadoAnexo = 1
  AND A.discriminador = 'I'
  AND u.PeriodoFacturacion <= ?
  AND u.Fecha_Proceso >= ?
ORDER BY u.PeriodoFacturacion, G.descripcion, A.NombreAnexo
"""
