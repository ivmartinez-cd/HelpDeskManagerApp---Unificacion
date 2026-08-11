# ADR-008: Advisory lock de Postgres para exclusión mutua en Equipos Offline

**Estado**: Aceptado  
**Fecha**: 2026-08-11  
**Afecta**: `backend/src/modules/insumos/`

---

## Contexto

Las operaciones de verify y delete de Equipos Offline pueden durar varios minutos (verify:
hasta 50 equipos × 2 s ≈ 100 s; delete: secuencial con confirmación del portal por equipo).
En un entorno con múltiples workers (uvicorn gunicorn), dos requests concurrentes podrían
ejecutarlas en paralelo, causando:

- **Verify doble**: mismo equipo consultado dos veces al SOAP en el mismo lote, con dos
  escrituras a `cd_status` que se pisan mutuamente.
- **Delete doble**: el equipo es válido en el snapshot del primer delete y del segundo;
  ambos llaman a `portal.delete_device()` — operación irreversible contra HP.

El legacy resolvía esto con un `threading.Lock` en memoria de proceso (`_verify_lock`). En un
entorno multi-proceso ese lock no funciona.

---

## Decisión

**Advisory lock de Postgres** (`pg_try_advisory_lock` / `pg_advisory_unlock`) sobre una
**conexión dedicada** tomada del engine en **`isolation_level="AUTOCOMMIT"`**.

---

## Opciones descartadas

### Tabla de locks propia

Requiere migración y mantenimiento. La limpieza de filas huérfanas después de un crash
es compleja. El advisory lock de Postgres hace todo eso por definición.

### Redis / Distributed lock

Introduce una dependencia de infraestructura nueva. Postgres ya está en el stack, y el
advisory lock ofrece las mismas garantías.

### La `AsyncSession` del request

Descartada por dos razones:
1. `get_db` hace commit al final del request. Si alguien introduce un commit intermedio
   en el futuro, la conexión vuelve al pool y el advisory lock queda huérfano hasta que
   muere el proceso — acoplamiento invisible que ningún test atrapa.
2. `pg_try_advisory_xact_lock` (atado a transacción) mantendría un snapshot abierto
   durante los 2-3 minutos del verify, bloqueando vacuum y reteniendo recursos.

### Conexión dedicada con `isolation_level="AUTOCOMMIT"`

El lock está atado a la sesión de Postgres (no a una transacción), así que:
- `pg_advisory_unlock` en el `finally` lo libera limpiamente, incluso ante excepciones.
- Si el proceso muere, Postgres libera el lock automáticamente al cerrar la sesión.
- No interfiere con el ciclo de commit/rollback del request principal.

---

## Claves de lock

Las claves viven en `infrastructure/locks/postgres_advisory_lock.py` como constantes
nombradas — registro central para que no queden dispersas. Cada par de operaciones
mutuamente excluyentes usa su propia clave:

```
OFFLINE_VERIFY_LOCK_KEY = 1_001_001
OFFLINE_DELETE_LOCK_KEY = 1_001_002
```

Verify y delete usan claves distintas deliberadamente: un verify en curso no debe
impedir que el operador inicie una baja (y viceversa). El riesgo de race es aceptable
— la validación de `deletable` es server-side y previa al DELETE real (ver §5 del plan).

Si un segundo módulo necesita advisory locks, el par `ExclusiveLock` + `PostgresAdvisoryLock`
se mueve a `shared/`.

---

## Consecuencias

- Comportamiento correcto en entorno multi-worker sin dependencias nuevas.
- Cada operación larga ocupa una conexión adicional del pool durante su duración.
  Con los defaults de SQLAlchemy (pool_size=5 + 10 overflow) esto es aceptable hoy.
- El puerto `ExclusiveLock` en dominio usa solo `contextlib.AbstractAsyncContextManager`
  (stdlib) — no viola el contrato `insumos-domain-no-frameworks`.
