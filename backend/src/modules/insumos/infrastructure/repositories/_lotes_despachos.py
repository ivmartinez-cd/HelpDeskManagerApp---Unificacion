"""Tamaño de lote de las altas de varias filas por sentencia de Insumos > Despachados."""

FILAS_POR_LOTE = 1000
"""asyncpg admite hasta 32767 parámetros por sentencia; el alta de un envío (la fila más
ancha, 25 columnas) entra holgada en 1000 filas. En una corrida normal hay una sola
sentencia por tabla: el lote solo corta la carga inicial de una ventana larga."""
