# ADR-043: Listas acotadas dentro de respuestas agregadas, sin `Page[T]`

## Estado: Aceptado (2026-10-01)

## Contexto

`ARCHITECTURE_GUIDE.md` §11.3 exige paginación en todo endpoint que devuelva una colección,
y `scripts/check_guards.py` lo verifica para los endpoints que devuelven `list[...]`. La
auditoría del 2026-09-30 encontró además colecciones **dentro** de un schema de respuesta
(un objeto con un campo `list[...]`), que el guard no ve y que no tenían ADR. ADR-011
(resumen de prestadores) y ADR-037 (tablero de proyección) ya habían aceptado casos
puntuales con el mismo razonamiento.

Revisados uno por uno, todos están acotados por naturaleza; ninguno alimenta una tabla
paginada en la UI:

| Endpoint / schema | Lista | Cota |
|---|---|---|
| contadores · `HistorialEquipoSchema.lecturas` | Lecturas de **un** equipo para su gráfico | Historial de un equipo |
| contadores · `CandidatosClientesNuevosResponse.candidatos` | Candidatos a cliente nuevo | Contratos recientes sin ficha (decenas) |
| insumos · `ConsumableHistoryResponse.points` | Serie del gráfico de nivel de **un** consumible | ~12 meses (rango de Insight) |
| insumos · `ConsumableRequestHistoryResponse.items` | Pedidos de **un** consumible | 12 meses |
| insumos · `AvailabilityWindowsResponse.windows` | Ventanas de disponibilidad de **un** equipo | Por equipo |
| liquidaciones · `RankingPrestadoresOut.items` | Ranking de prestadores | ~35 prestadores activos |
| liquidaciones · `PropuestasVinculoOut` (`propuestas`, `disponibles`) | Vincular prestadores con empresas de Siges (combobox) | Catálogo de prestadores / empresas |
| liquidaciones · `ZonasSigesOut.zonas` | Zonas de Siges | Catálogo de zonas |
| liquidaciones · `ResultadoWorklistTier2Out` (`certeza_absoluta`, `requiere_verificacion`) | Residuo de geovalidación de **un** prestador | ≤ filas de su tabla de km (máx. 1111 al 2026-10-01); para volumen grande existe el export CSV |
| vacaciones · `PropuestasVinculoResponse` (`propuestas`, `disponibles`) | Vincular empleados con técnicos de Siges (combobox) | Catálogo de empleados / técnicos |

## Decisión

1. Estas respuestas **quedan sin `Page[T]`**: son series de un gráfico, catálogos para un
   combobox o el resultado de una sola entidad. Partirlas en páginas rompería su uso
   (un gráfico o un selector necesitan la serie entera).
2. Condición para que la excepción siga valiendo: que la lista siga acotada por una sola
   entidad o por un catálogo chico. Si alguna empieza a mostrarse como **tabla paginada**,
   o su cota deja de ser natural (por ejemplo, la worklist de un prestador supera unos
   miles de filas), migra a `Page[T]` con su schema.
3. Un campo `list[...]` nuevo dentro de una respuesta **no** está cubierto por esta ADR:
   o va paginado, o se agrega a la tabla de arriba con su cota.

## Consecuencias

- Positivas: queda escrito por qué cada caso no se pagina y cuándo dejaría de valer.
- Negativas: `check_guards.py` sigue sin detectar listas dentro de schemas; esta tabla es
  el inventario y depende de la revisión al agregar un endpoint.
