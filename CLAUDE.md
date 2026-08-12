# CLAUDE.md

## Idioma y estilo de comunicación

Regla dura para toda respuesta de texto a el usuario en este repo (no aplica a nombres de
archivo, código, ni a los mensajes de commit, que siguen la convención en inglés ya establecida
en el historial de git).

- **Idioma**: español de Argentina, voseo natural. Sin lunfardo salvo pedido explícito. Otro
  idioma solo si el usuario lo pide expresamente.
- **Tono**: profesional, directo, conciso. Sin relleno.
- **Sin cortesías**: nada de saludos iniciales, frases tipo "¡Con gusto te ayudo!"/"¡Por
  supuesto!", ni cierres tipo "espero que te sea útil". Ir directo al contenido desde la primera
  palabra.
- **Cero alucinaciones**: nunca inventar datos, métricas, fuentes o información factual. Si
  falta información real, buscarla (web, código, comandos) antes de responder; si sigue sin ser
  verificable, decirlo explícitamente en vez de rellenar con una respuesta plausible pero
  infundada.

## Cumplimiento de ARCHITECTURE_GUIDE.md

Este repo tiene `ARCHITECTURE_GUIDE.md` en la raíz con reglas arquitectónicas obligatorias
(capas, manejo de errores, paginación, tamaños máximos, etc.). No es un documento de referencia
opcional: todo código nuevo tiene que cumplirlo **mientras se escribe**, no corregirse después
en una auditoría aparte. Concretamente:

- **Manejo de errores (§6)**: ningún `except Exception` puede quedar en silencio. Si el error se
  maneja devolviendo un fallback (no se relanza), loguear con `logging.getLogger(__name__)` y
  contexto relevante (`extra={...}`, `exc_info=exc`) en el punto donde se atrapa — no en el
  caller. Si no hay forma útil de manejarlo, dejarlo propagar o envolverlo en un error de dominio
  (`ExternalServiceError` y similares), nunca `except Exception: pass`.
- **Paginación (§11)**: todo endpoint que devuelva una colección (`list[...]`) va paginado, con
  el envelope genérico `Page[T]` de `src/shared/presentation/schemas/pagination.py` — no
  duplicar ese shape por módulo. Para catálogos chicos que alimentan un combobox con búsqueda en
  vivo (no una tabla paginada en la UI), un `size` default generoso es válido siempre que el
  contrato siga siendo paginado.
- **Tamaños máximos (§4)**: archivo ≤300 líneas, clase ≤200, función ≤20. Si un archivo se pasa,
  separar en módulos por responsabilidad en el momento, no siguiendo agregando al mismo archivo.
- **Verificación antes de dar por terminado un módulo** (no solo al final de todo el proyecto):
  correr, dentro del contenedor del backend —
  ```
  uv run lint-imports   # contratos de capas/módulos — la regla más importante, no es opinable
  uv run ruff check src tests
  uv run mypy src
  uv run pytest tests/unit -q
  ```
  Si algo de esto falla, no está terminado. `lint-imports` en particular es la única forma
  confiable de verificar la dirección de dependencias entre capas — no alcanza con revisar a
  ojo.
- Las desviaciones conscientes del texto literal de la guía se documentan como ADR en
  `backend/docs/adr/` (ver `007-vocabulario-de-permisos-en-shared-excepcion-de-presentation.md`
  como ejemplo) — una excepción sin ADR es una violación, no una decisión.

## Frontend en Docker: Turbopack no siempre recompila (caché stale)

`helpdesk-manager-frontend` corre en Docker (bind mount de `frontend/` a `/app`, ver
`docker-compose.yml`) con `next dev`/Turbopack. El file-watcher no siempre detecta ediciones: el
HTML servido y el bundle JS/CSS pueden seguir reflejando la versión anterior del código varios
minutos después de guardar, sin ningún error en `docker logs`. Pasó repetidas veces migrando
distintos módulos (2026-08-10, 2026-08-12), probablemente porque el watcher de Turbopack no
recibe eventos inotify fiables sobre un bind mount de Docker Desktop con host Windows (no
confirmado a nivel de causa raíz, solo el patrón observado).

**Cómo aplicar**: después de editar código de `frontend/` con el contenedor arriba, no asumir
que un cambio se refleja solo porque el navegador lo muestra (el navegador tiene su propia
caché). Verificar con curl antes de dar por buena una captura de pantalla o un test visual:

```
curl -s http://localhost:3000/<ruta> | grep <algo del cambio nuevo>
```

Si el curl sigue mostrando contenido viejo (o `docker logs helpdesk-manager-frontend --tail 5`
no muestra una recompilación reciente para esa ruta), `docker restart helpdesk-manager-frontend`
y esperar ~5-8s a que vuelva a responder 200 en `/` antes de re-verificar. No matar el contenedor
de forma permanente — es el servidor que se deja corriendo entre sesiones para que se pueda
probar en el navegador.
