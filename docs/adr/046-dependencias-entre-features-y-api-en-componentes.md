# ADR-046: Dependencias entre features y llamadas a la API desde componentes (frontend)

## Estado: Aceptado (2026-10-01)

## Contexto

`ARCHITECTURE_GUIDE.md` §2 organiza el frontend en `features/<feature>/` con `api/`,
`hooks/`, `components/` y `types/`, y §4 pide que un componente no mezcle fetch, estado y
layout. La auditoría del 2026-09-30 contó **90 imports cruzados entre features** y **118
componentes que llaman a la API** sin pasar por un hook, sin distinguir casos.

Revisados:

- **Imports cruzados.** La mayoría salen de dos features que *componen* otras, igual que
  `personas` en el backend (ADR-040): **Inicio** (`home`) arma cards con datos de
  contadores, SLA, turnos, vacaciones, insumos, WATI, bono y liquidaciones, y **Personas**
  combina la ficha de vacaciones con la cuenta de auth. El resto eran primitivos genéricos
  alojados en una feature (cards del dashboard en `home`, gráfico de tendencia en
  `insumos`), ya movidos a `shared/` (commits `d193d08c`, `ea18d715`), y unas pocas
  dependencias reales entre negocios.
- **API en componentes.** De 121 componentes, 87 solo llaman a la API **en un handler**
  (guardar, borrar, aprobar al apretar un botón). Los otros 34 **cargan datos al montarse**
  (`useEffect` + `useState` + fetch): ese es el caso que la guía quiere en un hook.

## Decisión

**Imports entre features** — se permiten solo estos, y siempre hacia `api/`, `types/`,
`hooks/` o `lib/` de la otra feature (nunca hacia sus `components/`):

1. Features de composición: `home` → cualquier feature; `personas` → `vacaciones` y
   `admin-users`.
2. Dependencias de negocio documentadas: `wati` → `turnos` (quién está de turno en ST),
   `tareas-varias` → `bono-tecnicos` (las tareas suman al bono), `sla` y `liquidaciones` →
   `prestadores` (catálogo de prestadores).
3. Todo lo demás compartido va a `shared/`. Un import cruzado nuevo fuera de esta lista es
   una violación, salvo que se agregue acá con su motivo.

**API desde componentes:**

- Llamar a la API **en un handler** de un componente está bien: es una acción del usuario y
  envolverla en un hook solo agrega indirección.
- **Cargar datos al montar** (`useEffect` con fetch y estado de carga/error) va en un hook
  de la feature (`features/<f>/hooks/use-*.ts`) que devuelve datos, `loading`, `error` y
  `refetch`; el componente solo renderiza.

## Consecuencias

- Positivas: la deuda queda acotada a casos concretos (34 componentes que cargan datos) en
  vez de 208 "violaciones" indiferenciadas; lo genérico vive en `shared/`.
- Negativas: el criterio no lo verifica una herramienta (no hay import-linter en el
  frontend); depende de la revisión.
