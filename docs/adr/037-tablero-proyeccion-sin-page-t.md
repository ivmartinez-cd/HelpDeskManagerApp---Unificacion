# ADR-037: Tablero de Proyección sin Page[T]

## Estado: Aceptado

## Contexto

`ARCHITECTURE_GUIDE.md` §11 exige paginación en todo endpoint que retorne colecciones, con
el envelope genérico `Page[T]` de `shared/presentation/schemas/pagination.py`.

`GET /api/contadores/proyeccion/tablero` (`presentation/proyeccion_router.py`) no lo usa:
devuelve `TableroProyeccionSchema`, un objeto con `resumen` (los cuatro totales del header:
reales/estimados/pendientes/sospechosos) y `filas: list[FilaProyeccionSchema]`, una fila por
equipo×clase de todo el parque de contadores del grupo/proceso pedido
(`GetTableroProyeccionUseCase.execute`,
`backend/src/modules/contadores/application/use_cases/get_tablero_proyeccion.py`). El shape
no es un `list[...]` en la firma del endpoint, así que el guard automático
(`scripts/check_guards.py`, regla `list-no-page`) no lo detecta por texto — pero el problema
de fondo que §11 busca evitar (nada limita cuántas filas puede devolver la respuesta) es el
mismo.

La tabla que consume esta respuesta (`frontend/src/features/contadores/components/
proyeccion-tabla.tsx`) ordena por columna con `SortableHeader`/`useTableSort` — el patrón
estándar del repo para "filtrar por columna" (ver regla de comunicación: toda tabla se
ordena con click-to-sort en el título, no con un panel de filtros por valor) — sobre el
array completo recibido, del lado del cliente. El legacy .NET/Blazor
(`GrillaEstimacion.razor`) hacía exactamente lo mismo: traía el parque completo del
grupo/proceso y ordenaba en el componente.

Se evaluaron dos opciones:

1. **`Page[FilaProyeccionSchema]`.** Cumple §11 literalmente, pero rompe el sort por columna:
   ordenar "impresiones" o "estim. propuesto" de una sola página no tiene sentido si hay
   filas con valores más altos en otra página — el operador necesita ver el parque completo
   ordenado para decidir dónde poner atención (equipos sospechosos, saltos imposibles), no
   una porción arbitraria. Paginar forzaría a mover el sort al backend (parámetro `sort_by` +
   `order`) solo para no romper una UX que hoy funciona sin eso.
2. **Mantener la respuesta como agregado de tablero**, igual que ADR-011 (prestadores) y
   ADR-021 (proxy SDS/Insight): un recurso "resumen + colección interna acotada por el
   tamaño real del negocio", no una colección paginada. El parque de contadores de un
   grupo/proceso es del orden de las decenas-centenas de equipos (acotado por la cantidad de
   clientes con contrato vigente, no una tabla transaccional que crece indefinidamente con el
   uso), y es exactamente lo que la pantalla necesita mostrar completo para que el sort por
   columna tenga sentido.

## Decisión

Opción 2. `GET /api/contadores/proyeccion/tablero` queda exceptuado de §11, leyendo la regla
igual que ADR-011/021: aplica a colecciones propias del dominio que se comportan como una
tabla transaccional, no a un tablero que la UI necesita completo para ordenar del lado del
cliente sobre la corrida entera.

Condiciones que revierten esta decisión:

1. Si el parque de un grupo/proceso deja de ser chico (referencia: >~1000 filas) y el payload
   se vuelve un problema real de performance o de memoria en el navegador.
2. Si el sort/filtro se mueve al backend por cualquier otro motivo (por ejemplo, búsqueda de
   texto libre sobre el parque completo de todos los grupos, no solo el seleccionado) — en
   ese momento paginar deja de tener el costo de romper el sort, porque el sort ya sería del
   backend.

Los sub-recursos de esta misma herramienta que sí son colecciones puras sin el condicionante
de sort completo (por ejemplo el historial de decisiones,
`proyeccion_historial_router.py`) siguen obligados a `Page[T]`.

## Consecuencias

- Positivas: una sola request trae el tablero completo con sort/filtro instantáneo del lado
  del cliente, sin duplicar esa lógica en el backend; paridad de comportamiento con el
  legacy que reemplaza.
- Negativas: el payload crece linealmente con el tamaño del parque del grupo/proceso pedido;
  no hay forma de pedir "una parte" del tablero ni de acotar el costo de la corrida completa
  del motor de estimación (`domain/services/estimacion/motor.py`) para procesos muy grandes.
- Revisar esta decisión si se cumple alguna de las condiciones de arriba.
