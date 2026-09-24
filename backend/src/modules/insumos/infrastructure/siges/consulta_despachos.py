"""Consulta a SiGesReadOnly de Insumos > Despachados (solo SELECT, parametrizada —
ARCHITECTURE_GUIDE §8). Esquema y filtros verificados con dato real el 2026-09-24 (ver
SIGES_READONLY_CATALOGO_DATOS.md §3 "Despachos OCA de insumos").

Por qué cada filtro:
- `ID_Distribucion IN (...)`: los transportes OCA que se siguen (hoy 3 OCA, 9 OCA SP,
  10 OCA Prioritario). Llegan como parámetro desde la configuración, no fijos en el SQL.
- `TipoRemito = 'I'`: solo remitos de insumos. Los 'R' son repuestos (fusores, rodillos,
  bandejas), nunca enlazan a un pedido de insumos y quedan fuera de este seguimiento.
- `LEN(Guia) = 19` + `Guia NOT LIKE '%[^0-9]%'`: la guía OCA rastreable tiene exactamente
  19 dígitos. Así quedan afuera los remitos cargados con "FALTA" y cualquier guía mal
  tipeada, que OCA no podría encontrar.
- `Fecha_Remito` dentro de los últimos `dias_ventana` días, contados desde hoy a las 00:00
  del servidor.

Joins:
- LEFT JOIN a `Incidente_Insumo_D`/`Incidente_Insumo_C`: un remito sin incidente
  vinculado igual se sigue en OCA; no se pierde el envío, queda sin incidentes.
  `Incidente_Insumo_D` tiene una fila por ítem, así que un incidente con varios ítems en
  el mismo remito repite filas: el DISTINCT las colapsa y `mapeo_despachos` agrupa por
  remito los que llevan más de un incidente.
- LEFT JOIN a `Empresa`/`Sucursal`: nombre del cliente y de su sucursal, informativos;
  no deben filtrar remitos.

Orden de los parámetros: primero una `?` por distribución, al final `dias_ventana`.
"""

PLANTILLA_DESPACHOS_OCA_SQL = """
SELECT DISTINCT
       rc.Id_Remito AS id_remito,
       rc.Remito_Nro AS numero_remito,
       rc.Guia AS guia,
       rc.ID_Distribucion AS id_distribucion,
       rc.Fecha_Remito AS fecha_remito,
       rc.Bultos AS bultos,
       rc.Entrega_a AS entrega_a,
       e.Den_Comercial AS cliente,
       s.Descripcion AS sucursal_cliente,
       c.NroIncidente AS numero_incidente,
       c.Nro_Incidente_Cliente AS numero_incidente_cliente
FROM dbo.Remito_Cab rc
LEFT JOIN dbo.Incidente_Insumo_D d ON d.ID_Remito = rc.Id_Remito
LEFT JOIN dbo.Incidente_Insumo_C c ON c.ID_Incidente_Insumo = d.ID_Incidente_Insumo
LEFT JOIN dbo.Empresa e ON e.ID_Empresa = rc.Id_Empresa
LEFT JOIN dbo.Sucursal s ON s.Id_Sucursal = rc.Id_Sucursal
WHERE rc.ID_Distribucion IN ({marcadores})
  AND rc.TipoRemito = 'I'
  AND LEN(rc.Guia) = 19
  AND rc.Guia NOT LIKE '%[^0-9]%'
  AND rc.Fecha_Remito >= DATEADD(day, -?, CAST(GETDATE() AS date))
ORDER BY fecha_remito DESC, id_remito, numero_incidente
"""


def construir_consulta_despachos(cantidad_distribuciones: int) -> str:
    """SQL con una `?` por distribución en el IN (un `IN ()` vacío no es SQL válido)."""
    if cantidad_distribuciones < 1:
        raise ValueError("Hace falta al menos una distribución para consultar despachos")
    marcadores = ", ".join("?" for _ in range(cantidad_distribuciones))
    return PLANTILLA_DESPACHOS_OCA_SQL.format(marcadores=marcadores)
