# ADR-009: Inyección cruzada auth → contadores (color de operador) vía `dependency_overrides`

## Estado: Aceptado

## Contexto

Al dar de alta un usuario (`CreateUser`, módulo `auth`), la app necesita resolver el color de
identidad que esa persona ya tiene como operador de Gestión — dato que hoy solo existe en
`contadores_operadores` (tabla del módulo `contadores`, poblada por el sync del Calendario de
Contadores). El caso de uso `CreateUser` necesita, entonces, un puerto que le devuelva "el color
de este nombre en Gestión, si existe".

El contrato `auth-independent-from-contadores` de `.importlinter` (ver ADR-007) prohíbe que
**cualquier cosa bajo `src.modules.auth`** importe `src.modules.contadores` — a diferencia del
contrato de `contadores`/`auth`, acá no hay excepción de capa ya perforada, y la dirección
necesaria (`auth` ← `contadores`) es la inversa de la que resolvió ADR-007.

Primer intento: definir el puerto `OperadorColorLookup` en `auth.domain` (correcto, es
vocabulario de auth) e implementarlo en un adaptador nuevo dentro de `src/shared/infrastructure/`
(que sí puede importar cualquier módulo de negocio), importado directo desde
`admin_users_router.py`. **`lint-imports` lo marcó roto**: el contrato analiza el grafo de
imports de forma transitiva, no solo imports directos — `auth.presentation.admin_users_router →
shared.infrastructure.cross_module.auth_operador_color_lookup → contadores...` sigue siendo un
camino `auth → contadores`, aunque pase por `shared`. No hay forma de que un adaptador con la
dependencia real, importado estáticamente desde cualquier archivo de `auth`, deje de contar.

## Decisión

Romper el camino estático con inyección de dependencias en tiempo de ejecución (patrón nativo de
FastAPI, `app.dependency_overrides`), no con un import:

1. `auth.domain.repositories.operador_color_lookup.OperadorColorLookup` — el `Protocol`, puro,
   sin imports de contadores (esto no cambia respecto al primer intento).
2. `auth.presentation.dependencies.operador_colors.get_operador_color_lookup` — una función
   `Depends`-compatible que vive dentro de `auth` y **solo importa el Protocol de su propio
   módulo**. Su cuerpo por default levanta `NotImplementedError` — nunca se ejecuta en la app
   real, es una señal de wiring faltante si alguna vez se llama sin override.
3. `shared.infrastructure.cross_module.auth_operador_color_lookup.SqlAlchemyOperadorColorLookup`
   — el adaptador real, que sí importa `contadores.infrastructure...SqlAlchemyCalendarEvent
   Repository`. Vive en `shared` porque es el único punto del repo sin restricciones de
   import-linter hacia ningún módulo de negocio.
4. `shared.presentation.app.py` (la raíz de composición) importa **ambos lados** — el
   `get_operador_color_lookup` de auth y el `SqlAlchemyOperadorColorLookup` de shared — y los
   conecta con `app.dependency_overrides[get_operador_color_lookup] = _provide_operador_color_
   lookup` al construir la app. Como `app.py` no es parte de ningún `source_modules` restringido,
   este es el único archivo del repo con permiso de conocer a la vez a `auth` y `contadores`
   para este caso.

El router de `auth` (`admin_users_router.py`) sigue sin importar nada de `contadores`, ni directa
ni transitivamente: solo conoce `get_operador_color_lookup` (de su propio módulo) y recibe la
implementación real vía `Depends(...)`, resuelta por el override de `app.py` en tiempo de
ejecución — invisible para `lint-imports`, que solo analiza imports estáticos.

## Consecuencias

- Positivas: `lint-imports` queda limpio sin perforar ni modificar el contrato
  `auth-independent-from-contadores` — la garantía que protege (que `auth` se pueda extraer o
  testear sin `contadores`) sigue siendo real, no solo textual. El patrón es reusable: cualquier
  otro cruce `auth ← módulo-de-negocio` futuro sigue el mismo molde (Protocol en auth,
  `NotImplementedError` como placeholder, override real en `app.py`).
- Negativas: una capa de indirección más que un import directo — para entender qué implementación
  corre en runtime hay que mirar `app.py`, no alcanza con seguir el import del router. Si el
  placeholder alguna vez se ejecuta sin override (test que arma la app sin pasar por
  `create_app()`, por ejemplo), falla con `NotImplementedError` en vez de un error de import más
  temprano — es un fallo en runtime, no en tiempo de carga.
- Revisar esta decisión si aparecen 2-3 casos más de cruces `auth ← módulo-de-negocio`: en ese
  punto valdría la pena un helper genérico en `shared` para registrar overrides en vez de
  repetir el patrón a mano en `app.py` cada vez.
