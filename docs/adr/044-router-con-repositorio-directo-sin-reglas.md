# ADR-044: Router con repositorio directo cuando no hay regla de negocio

## Estado: Aceptado (2026-10-01)

## Contexto

`ARCHITECTURE_GUIDE.md` §3 pone los casos de uso en `application` y deja a `presentation`
la serialización, la autenticación y el routing. La auditoría del 2026-09-30 contó **59
llamadas directas a repositorios desde routers** (33 en liquidaciones). ADR-038 y ADR-041 ya
habían aceptado ese patrón para casos puntuales ("no hay regla de negocio más allá de
filtrar y paginar"), pero sin un criterio general, así que cada caso nuevo quedaba como
violación aparente.

Revisadas las de liquidaciones, son listados de catálogos (`list_all`, `list_periodos`),
agregados para gráficos (`sum_importe_por_periodo`, `count_pendientes_por_prestador`) y
escrituras de un solo campo sin invariantes (`marcar_vistas`, `set_activa`,
`vincular_cd`). Envolver cada una en un caso de uso que solo delega agrega una clase, un
archivo y un test por endpoint sin mover ninguna regla: es el patrón que la propia guía
llama *YAGNI* y que la regla de oro "si agregar una feature requiere tocar más de 2 archivos
no relacionados, la arquitectura está mal" desaconseja.

## Decisión

Un router **puede** llamar directo a un repositorio (instanciado en presentation, que es el
punto de composición) cuando la operación es:

1. una **lectura** sin reglas: listar, filtrar, paginar, agregar para un gráfico; o
2. una **escritura de un campo** que no tiene invariantes ni efectos derivados (marcar
   visto, activar/desactivar, guardar un vínculo elegido por el usuario).

Tiene que ir a un **caso de uso** en `application` cuando la operación:

- valida o decide algo del negocio (estados, permisos por alcance, cálculos, duplicados);
- toca más de un agregado o más de un repositorio con coherencia entre ellos;
- dispara efectos (mails, notificaciones, llamadas a servicios externos, reanálisis);
- parsea o arma datos de negocio (importaciones, conversiones, reglas de matching).

La lógica de negocio que hoy vive en `presentation` (`_liq_csv*.py` de liquidaciones,
`_proyeccion_*.py` de contadores) **no** queda cubierta por esta ADR: se mueve a
`application`. El armado de archivos con librerías de terceros (`_reportes_export.py` de
vacaciones, fpdf/openpyxl) se mueve a `infrastructure` (§5: dependencias externas aisladas).

## Consecuencias

- Positivas: el criterio queda escrito; las 59 llamadas se separan en aceptadas (la
  mayoría) y a mover, en vez de una deuda indiferenciada.
- Negativas: el límite es de juicio, no lo verifica ninguna herramienta. Ante la duda,
  caso de uso.
