# ADR-011: Listado de prestadores como resumen agregado, no paginado

## Estado: Aceptado

## Contexto

`ARCHITECTURE_GUIDE.md` §11 exige paginación en todo endpoint que retorne colecciones, con el
envelope genérico `Page[T]` de `shared/presentation/schemas/pagination.py`. La excepción
operativa acordada para catálogos chicos (ver CLAUDE.md) permite un `size` default generoso
**siempre que el contrato siga siendo paginado**.

`GET /api/prestadores` no cumple ninguna de las dos formas: devuelve
`PrestadoresResumenResponse` — cuatro totales globales (`totalPrestadores`, `totalActivos`,
`operadoresConPst`, `sinAsignar`) más `grupos`, la lista de operadores con sus PST anidados.
Es el shape que consume la única vista que lo usa: el tablero de prestadores agrupado por
operador, que se muestra siempre completo (el catálogo real es ~24 PST, acotado por la
cantidad de técnicos del canal — no crece con el uso como una tabla transaccional).

Se evaluaron tres opciones:

1. **`Page[PrestadorDTO]` plano** + agrupar por operador en el cliente + un endpoint aparte
   para los totales. Cumple §11 literalmente, pero parte una sola pantalla en dos requests
   cuyos datos pueden quedar inconsistentes entre sí (los totales de una foto, los grupos de
   otra), y mueve al cliente una agregación que es lógica de presentación del backend.
2. **`Page[OperadorGroup]`** (paginar los grupos). Mantiene el envelope pero no resuelve
   nada: los totales siguen siendo globales (no de la página), y cortar un tablero de ~10
   grupos por la mitad no tiene sentido de producto.
3. **Mantener el agregado**: tratar la respuesta como un recurso "resumen" (un objeto), no
   como una colección. Las colecciones internas están acotadas por el tamaño natural del
   catálogo, y los sub-recursos que sí son colecciones puras ya paginan con `Page[T]`
   (`GET /api/prestadores/operadores`, `GET /api/prestadores/{id}/historial`).

## Decisión

Opción 3. `GET /api/prestadores` queda como recurso resumen con shape agregado; la regla de
§11 se lee como aplicable a endpoints cuyo recurso **es** una colección, no a agregados de
tablero con colecciones internas acotadas. Todo endpoint nuevo del módulo que devuelva una
colección pura sigue obligado a `Page[T]` (como ya hacen `/operadores` e `/historial`).

## Consecuencias

- Positivas: una sola request para el tablero completo; totales y grupos siempre
  consistentes entre sí (misma foto); el contrato expresa lo que la UI realmente es.
- Negativas: el payload crece linealmente con el catálogo de PST; no hay forma de pedir "una
  parte" del tablero.
- Revisar esta decisión si el catálogo deja de ser chico (referencia: >~200 PST) o si
  aparece una segunda vista que necesite los prestadores como lista plana — en ese momento
  migrar a la opción 1 (colección paginada + endpoint de totales) deja de ser sobrecosto y
  pasa a ser lo correcto.
