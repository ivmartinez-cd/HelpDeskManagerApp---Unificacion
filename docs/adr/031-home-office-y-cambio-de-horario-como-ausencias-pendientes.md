# ADR-031: Home office y cambio de horario se piden como ausencias PENDING, las aprueba la TL e impactan en Turnos

## Estado: Aceptado (2026-08-21)

## Contexto

Pedido del usuario al configurar a los operadores de mesa de ayuda: que desde "Solicitudes" de
Gestión de Personal puedan pedir **home office** y **cambios de horario puntuales** (ej. Victor la
semana que viene trabaja 8–17 en vez de 9–18), que **siempre pasen por la TL**, que queden en el
**Registro de asistencias** y que **Turnos** se entere.

Lo que había: `Solicitud` era solo de vacaciones (días, saldo, año imputado) con circuito
PENDING → APPROVED/REJECTED; `Ausencia` ("Registro de asistencias") ya tenía `status` con los
mismos tres estados y tipo `HOME_OFFICE`, pero la cargaba solo el admin/jefe y **nacía APPROVED**;
no existía "cambio de horario". Turnos solo conocía las vacaciones aprobadas, vía el puerto
`AusenciasLookup` (ADR-025), para advertir huecos en el editor de grilla variante.

## Decisión

1. **No hay entidad nueva**: una solicitud de home office / cambio de horario **es una `Ausencia`**
   que el empleado crea para sí mismo y nace **PENDING** (`estado_inicial(actor)`: admin/jefe
   siguen registrando hechos APPROVED). Se decide con `DecidirAusencia` /
   `POST /api/vacaciones/ausencias/{id}/decision` (permiso `vacaciones.approve`, mismos alcances
   que las vacaciones: admin todo, jefe su sector, nadie se aprueba a sí mismo; auditado). Al
   aprobarse ya está en el Registro de asistencias: no hay sincronización.
2. Tipo nuevo **`CAMBIO_HORARIO`** con `hora_desde`/`hora_hasta` obligatorias (migración
   `b8d1f4c7a2e9`, check constraint); `validar_horario` en dominio. Es una "novedad", no una
   ausencia del día: el operador trabaja, pero en otra ventana.
3. **Impacto en Turnos** (dirección vacaciones → turnos, misma del ADR-025): `AusenciasLookup`
   devuelve vacaciones **y** ausencias aprobadas con `tipo` + horas. Con eso:
   - "Turnos del día" (`GetCurrentShifts`) anota a cada operador con la novedad del día
     (`nota`: 'Home office', 'Horario 08:00–17:00', 'Vacaciones'…) → badge en la card de Inicio.
   - El editor de grilla variante advierte con `detalle` (home office no genera advertencia: no
     saca a nadie de la grilla; un cambio de horario advierte "fuera de ese horario no va a poder
     cubrir").
   - Al aprobar una novedad, la decisión devuelve `afectaTurnos` si el empleado tiene franjas en
     el rango, y el frontend ofrece el mismo CTA "Armar grilla de cobertura" que las vacaciones.
   La grilla **no se toca sola** (criterio humano, como en ADR-025).
4. Frontend: "Mis Solicitudes" gana la sección **Home office y horario**; "Aprobaciones" gana la
   lista de novedades pendientes; el Registro de asistencias muestra estado y horario; el
   calendario solo pinta lo aprobado.

## Consecuencias

- Positivas: cero duplicación (un solo modelo, un solo listado de asistencias, un solo circuito
  de aprobación); Turnos refleja cualquier ausencia aprobada (también enfermedad, trámite), no
  solo vacaciones.
- Negativas/costos: cambia el comportamiento de "un empleado registra su propia baja": antes
  nacía aprobada (paridad legacy), ahora queda pendiente — decisión explícita del usuario. Un
  cambio de horario no modifica franjas: si la TL quiere reasignar, usa coberturas/grilla
  variante desde el CTA.
- Pendiente (no pedido): notificación por mail al decidir una novedad (las vacaciones sí la
  tienen), topes de home office por semana.
