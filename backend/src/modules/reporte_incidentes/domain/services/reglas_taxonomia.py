"""Conjuntos especiales de subcategorías (port literal de `taxonomy.v1.ts`,
TAXONOMY_VERSION v1.6-2026-06-24). Los nombres tienen que coincidir exacto con
los de la taxonomía configurada: son los que devuelve la tipificación."""

VERSION_TAXONOMIA = "v1.6-2026-06-24"

# Casos cuya causa de fondo NO está en el equipo.
SUBCATEGORIAS_FUERA_DEL_EQUIPO = frozenset({
    "Papel inadecuado / humedad / mala calidad",
    "Papel especial / Troquelado",
    "Mal uso / Negligencia",
    "Problema externo / Red del cliente",
    "Mesa de ayuda / Sin respuesta del cliente",
    # El equipo imprime bien: falla el driver o la cola de impresión de la PC.
    "Driver / PC / Spooler",
    # Se revisó y no había falla que reparar.
    "Diagnostico / Sin falla",
    # Se cerró enviando un instructivo o un video; el equipo nunca falló.
    "Instructivo / Autoresolucion",
    # Red de la sucursal (cortes, bocas, VPN). Evidencia ambigua en el corpus:
    # se muestra, pero no se presenta como causa cerrada.
    "Configuracion de red / IP",
})

# Subconjunto más fuerte: visitas que se cerraron SIN reparar el equipo. Es el
# titular de "Oportunidades de Mejora": una visita que no terminó en reparación
# se podía haber resuelto en remoto o filtrado en la apertura del ticket.
SUBCATEGORIAS_SIN_REPARACION = frozenset({
    "Diagnostico / Sin falla",
    "Instructivo / Autoresolucion",
    "Driver / PC / Spooler",
})
