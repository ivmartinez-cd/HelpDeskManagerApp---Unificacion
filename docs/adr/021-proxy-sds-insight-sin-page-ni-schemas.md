# ADR-021: Endpoints proxy de SDS/Insight sin Page[T] ni schemas propios

## Estado: Aceptado (2026-08-16) — condición 3 ejecutada el mismo día:
`GET /clients` se borró (sin consumidor, YAGNI) junto con su cadena
(`GetFleetClients`, `get_customers` del puerto e implementación). El alcance de
esta ADR queda en los cinco endpoints restantes.

## Contexto

`analisis_log_hp/presentation/sds_router.py` expone seis endpoints que devuelven
`list[dict[str, Any]]` sin el envelope `Page[T]` (§11) ni schemas Pydantic de salida:

- `GET /devices/{id}/consumables`, `/alerts`, `/meters`, `/hp-operations` —
  sub-recursos de **un** equipo, acotados por naturaleza (una impresora tiene un
  puñado de consumibles/alertas/operaciones; meters ya acota por `days<=365`).
- `GET /clients` y `GET /clients/{id}/devices` — catálogo de clientes de la flota
  del canal y equipos de un cliente, acotados por el tamaño del negocio (decenas,
  no una tabla transaccional que crece con el uso).

Los seis son **proxies de lectura** sobre HP Insight (vía el gateway compartido):
el shape de cada respuesta lo define el sistema externo, el backend no lo
transforma ni lo persiste, y la UI (paneles de detalle del análisis de logs) lo
consume como JSON semi-libre — el único endpoint con shape estable tipado en el
frontend es `/clients/{id}/devices` (`ClientDevice`). `GET /clients` hoy no tiene
ningún consumidor en `frontend/src`.

Definir schemas Pydantic propios significaría fijar en nuestro contrato campos que
Insight puede cambiar (el legacy ya sufrió renombres), rompiendo el proxy con
validación 500 en vez de degradar con gracia. Paginar colecciones que el upstream
entrega completas en una llamada agregaría un envelope sin recorte real de payload.

## Decisión

Los seis endpoints del proxy SDS/Insight quedan **exceptuados de §11 (Page[T]) y del
tipado de salida con schemas**, leyendo la regla igual que ADR-011: aplica a
colecciones propias del dominio, no a passthroughs acotados de un sistema externo
cuyo shape no nos pertenece.

Condiciones que revierten esta decisión (por endpoint):

1. Si el backend empieza a **transformar o persistir** la respuesta (deja de ser un
   passthrough), el shape pasa a ser nuestro y se tipa con schema.
2. Si una vista lo consume como **tabla paginada** en la UI, ese endpoint migra a
   `Page[T]` con schema.
3. Si `GET /clients` sigue sin consumidor en la próxima auditoría, evaluar borrarlo
   (YAGNI) en vez de mantenerlo exceptuado.

## Consecuencias

- La desviación de §11/tipado queda con registro explícito en vez de ser una
  violación silenciosa.
- El costo asumido: OpenAPI no documenta el shape real de estas respuestas — quien
  las consuma debe mirar Insight. Aceptable mientras el único consumidor sea el
  feature de análisis de logs.
