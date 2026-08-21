"""SQL de las fichas de clientes nuevos contra SiGesReadOnly (solo lectura,
placeholders pyodbc — ARCHITECTURE_GUIDE §8). Señales verificadas el
2026-08-21 (SIGES_READONLY_CATALOGO_DATOS.md §3, "cliente nuevo"):

- `MaquinaUFisica` con `ID_MotivoMov = 1` ('Alta en Cliente') la carga
  Equipamiento **al despachar** la máquina (mismo día: toma tipo 8 "Contador
  Inicial" e incidente 103 en estado 200 Derivado). NO confirma que el equipo
  esté instalado: en el interior puede seguir en viaje. Por eso acá es
  "despachada".
- La instalación se confirma cuando el PST cierra el incidente 103 de esa
  máquina (estado 500/600/700/710 — a veces sin `Fecha_Cierre`, con
  `PlanillaIT`) o cuando aparece una toma real (`ID_TipoToma NOT IN (8, 13,
  14, 19)`) posterior al alta. Medido en 90 días: 493 de 1065 altas
  confirmadas por alguna de las dos; las no confirmadas son cargas masivas
  sin incidente (Natura, Exolgan…) o despachos recientes.
- `Empresa` no tiene fecha de alta: "cliente nuevo" = empresa cuyo primer
  `Contrato.FechaFirmaContrato` es reciente. Rubro por `Contrato.ID_EmpresaAdmin`.
"""

_ALTAS_CTE = """
WITH altas AS (
    SELECT U.ID, U.ID_Maquina, U.ID_Empresa, U.Fecha_Movim
    FROM dbo.MaquinaUFisica U
    WHERE U.ID_MotivoMov = 1 AND U.ID_Empresa IN ({placeholders})
),
conf AS (
    SELECT A.ID, A.ID_Maquina, A.ID_Empresa, A.Fecha_Movim,
           CASE WHEN EXISTS (
               SELECT 1 FROM dbo.Incidente I
               WHERE I.ID_Maquina = A.ID_Maquina AND I.ID_Empresa = A.ID_Empresa
                 AND I.ID_Tipo_Incidente = 103
                 AND I.ID_Estado_Incidente IN (500, 600, 700, 710)
                 AND I.Fecha_Ingreso >= DATEADD(day, -7, A.Fecha_Movim)
           ) THEN 1 ELSE 0 END AS inc_cerrado,
           (SELECT MAX(I.Fecha_Cierre) FROM dbo.Incidente I
             WHERE I.ID_Maquina = A.ID_Maquina AND I.ID_Empresa = A.ID_Empresa
               AND I.ID_Tipo_Incidente = 103
               AND I.ID_Estado_Incidente IN (500, 600, 700, 710)
               AND I.Fecha_Cierre > '1901-01-01'
               AND I.Fecha_Ingreso >= DATEADD(day, -7, A.Fecha_Movim)) AS fecha_cierre,
           (SELECT MIN(C.FechaTomaContador) FROM dbo.Contadores C
             WHERE C.ID_Maquina = A.ID_Maquina AND C.ID_Empresa = A.ID_Empresa
               AND C.Estado = 0 AND C.ID_TipoToma NOT IN (8, 13, 14, 19)
               AND C.FechaTomaContador >= A.Fecha_Movim) AS primera_real
    FROM altas A
),
resumen AS (
    SELECT ID_Empresa,
           COUNT(DISTINCT ID_Maquina) AS equipos_despachados,
           MAX(Fecha_Movim) AS ultimo_despacho,
           COUNT(DISTINCT CASE WHEN inc_cerrado = 1 OR primera_real IS NOT NULL
                               THEN ID_Maquina END) AS equipos_instalados,
           MAX(COALESCE(fecha_cierre, primera_real)) AS ultima_instalacion,
           COUNT(DISTINCT CASE WHEN primera_real IS NOT NULL THEN ID_Maquina END)
               AS equipos_con_toma,
           (SELECT COUNT(DISTINCT MI.NroInstala) FROM dbo.MaquinaInstalacion MI
             INNER JOIN altas A2 ON A2.ID = MI.ID_UFisica
             WHERE A2.ID_Empresa = conf.ID_Empresa) AS instalas
    FROM conf
    GROUP BY ID_Empresa
)
"""

RESUMEN_INSTALACIONES_SQL = (
    _ALTAS_CTE
    + """
SELECT E.ID_Empresa AS empresa_id,
       COALESCE(R.equipos_despachados, 0) AS equipos_despachados,
       R.ultimo_despacho,
       COALESCE(R.equipos_instalados, 0) AS equipos_instalados,
       R.ultima_instalacion,
       COALESCE(R.equipos_con_toma, 0) AS equipos_con_toma,
       COALESCE(R.instalas, 0) AS instalas,
       CT.NombreContrato AS contrato_nro,
       CT.FechaFirmaContrato AS fecha_firma,
       CT.ID_EmpresaAdmin AS id_empresa_admin,
       V.Descripcion AS vendedor
FROM dbo.Empresa E
LEFT JOIN resumen R ON R.ID_Empresa = E.ID_Empresa
OUTER APPLY (
    SELECT TOP 1 C.NombreContrato, C.FechaFirmaContrato, C.ID_EmpresaAdmin, C.Id_Vendedor
    FROM dbo.Contrato C
    WHERE C.ID_Empresa = E.ID_Empresa
    ORDER BY C.FechaFirmaContrato DESC, C.ID_Contrato DESC
) CT
LEFT JOIN dbo.Vendedor V ON V.Id_Vendedor = CT.Id_Vendedor
WHERE E.ID_Empresa IN ({placeholders})
"""
)

# Empresas cliente (101 general / 102 grandes cuentas) con un contrato firmado
# desde la fecha dada y SIN contratos anteriores a esa fecha = primer contrato
# reciente. Si una empresa firmó dos en la ventana, el gateway se queda con el
# más viejo. `equipos_despachados` = altas en cliente (no confirma instalación).
CANDIDATOS_SQL = """
SELECT E.ID_Empresa AS empresa_id,
       E.Den_Comercial AS cliente,
       C.NombreContrato AS contrato_nro,
       C.FechaFirmaContrato AS fecha_firma,
       C.ID_EmpresaAdmin AS id_empresa_admin,
       V.Descripcion AS vendedor,
       (SELECT COUNT(DISTINCT U.ID_Maquina) FROM dbo.MaquinaUFisica U
         WHERE U.ID_Empresa = E.ID_Empresa AND U.ID_MotivoMov = 1) AS equipos_despachados
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
    # Los ids van dos veces (CTE y SELECT final): el gateway duplica los params.
    return RESUMEN_INSTALACIONES_SQL.format(placeholders=", ".join("?" * cantidad))
