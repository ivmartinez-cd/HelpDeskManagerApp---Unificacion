"""SQL de las fichas de clientes nuevos contra SiGesReadOnly (solo lectura,
placeholders pyodbc — ARCHITECTURE_GUIDE §8). Señales verificadas el
2026-08-21 (SIGES_READONLY_CATALOGO_DATOS.md §3, "cliente nuevo"):

- El registro real de una instalación es `MaquinaUFisica` con
  `ID_MotivoMov = 1` ('Alta en Cliente'; `MaquinaInstalacion.NroInstala`
  agrupa las máquinas de una misma instala) — NO el incidente tipo 103, que
  es la orden de trabajo por máquina y no distingue instalación de
  desinstalación.
- `Empresa` no tiene fecha de alta: "cliente nuevo" = empresa cuyo primer
  `Contrato.FechaFirmaContrato` es reciente. El rubro sale de
  `Contrato.ID_EmpresaAdmin` (ver `rubro_empresa_admin.py`).
- `Fecha_Mod` de las vistas emuladas (`Empresa`, `Contrato`, `Anexo`) trae
  la hora del refresh de la réplica: no se usa.
"""

RESUMEN_INSTALACIONES_SQL = """
SELECT E.ID_Empresa AS empresa_id,
       (SELECT COUNT(DISTINCT U.ID_Maquina) FROM dbo.MaquinaUFisica U
         WHERE U.ID_Empresa = E.ID_Empresa AND U.ID_MotivoMov = 1) AS equipos_instalados,
       (SELECT COUNT(DISTINCT MI.NroInstala) FROM dbo.MaquinaUFisica U
         INNER JOIN dbo.MaquinaInstalacion MI ON MI.ID_UFisica = U.ID
         WHERE U.ID_Empresa = E.ID_Empresa AND U.ID_MotivoMov = 1) AS instalas,
       (SELECT MIN(U.Fecha_Movim) FROM dbo.MaquinaUFisica U
         WHERE U.ID_Empresa = E.ID_Empresa AND U.ID_MotivoMov = 1) AS primera_instalacion,
       (SELECT MAX(U.Fecha_Movim) FROM dbo.MaquinaUFisica U
         WHERE U.ID_Empresa = E.ID_Empresa AND U.ID_MotivoMov = 1) AS ultima_instalacion,
       (SELECT COUNT(DISTINCT C.ID_Maquina) FROM dbo.Contadores C
         WHERE C.ID_Empresa = E.ID_Empresa AND C.Estado = 0) AS equipos_con_toma,
       CT.NombreContrato AS contrato_nro,
       CT.FechaFirmaContrato AS fecha_firma,
       CT.ID_EmpresaAdmin AS id_empresa_admin,
       V.Descripcion AS vendedor
FROM dbo.Empresa E
OUTER APPLY (
    SELECT TOP 1 C.NombreContrato, C.FechaFirmaContrato, C.ID_EmpresaAdmin, C.Id_Vendedor
    FROM dbo.Contrato C
    WHERE C.ID_Empresa = E.ID_Empresa
    ORDER BY C.FechaFirmaContrato DESC, C.ID_Contrato DESC
) CT
LEFT JOIN dbo.Vendedor V ON V.Id_Vendedor = CT.Id_Vendedor
WHERE E.ID_Empresa IN ({placeholders})
"""

# Empresas cliente (101 general / 102 grandes cuentas) con un contrato firmado
# desde la fecha dada y SIN contratos anteriores a esa fecha = primer contrato
# reciente. Si una empresa firmó dos en la ventana, el gateway se queda con el
# más viejo.
CANDIDATOS_SQL = """
SELECT E.ID_Empresa AS empresa_id,
       E.Den_Comercial AS cliente,
       C.NombreContrato AS contrato_nro,
       C.FechaFirmaContrato AS fecha_firma,
       C.ID_EmpresaAdmin AS id_empresa_admin,
       V.Descripcion AS vendedor,
       (SELECT COUNT(DISTINCT U.ID_Maquina) FROM dbo.MaquinaUFisica U
         WHERE U.ID_Empresa = E.ID_Empresa AND U.ID_MotivoMov = 1) AS equipos_instalados
FROM dbo.Contrato C
INNER JOIN dbo.Empresa E ON E.ID_Empresa = C.ID_Empresa
LEFT JOIN dbo.Vendedor V ON V.Id_Vendedor = C.Id_Vendedor
WHERE E.ID_Tipo_Empresa IN (101, 102)
  AND C.FechaFirmaContrato >= ?
  AND NOT EXISTS (
      SELECT 1 FROM dbo.Contrato C0
      WHERE C0.ID_Empresa = C.ID_Empresa AND C0.FechaFirmaContrato < ?
  )
ORDER BY C.FechaFirmaContrato ASC, C.ID_Contrato ASC
"""


def build_resumen_instalaciones_sql(cantidad: int) -> str:
    return RESUMEN_INSTALACIONES_SQL.format(placeholders=", ".join("?" * cantidad))
