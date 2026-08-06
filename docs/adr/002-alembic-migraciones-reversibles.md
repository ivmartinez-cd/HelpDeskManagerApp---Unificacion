# ADR-002: Alembic para migraciones — se prohíbe `Base.metadata.create_all`

## Estado: Aceptado

## Contexto

El backend padre (`HelpDeskManager-Web/backend/database.py`) no usa ninguna herramienta de
migraciones: crea el schema con `Base.metadata.create_all(bind=engine)`, invocado además
dos veces (`main.py:67` y `main.py:230`). Esto crea tablas nuevas pero no altera las
existentes — cualquier cambio de columna en producción requiere intervención manual sin
registro ni posibilidad de rollback. `ARCHITECTURE_GUIDE.md` §12 exige que las migraciones
de DB sean reversibles (down migration).

## Decisión

Usamos Alembic para todo el schema, desde la primera tabla. `Base.metadata.create_all`
queda prohibido en este proyecto. Toda migración debe tener `upgrade()` y `downgrade()`
funcionales — se verifica corriendo `alembic downgrade base` después de cada `upgrade head`
antes de dar la migración por cerrada (ver Etapa 3 y 4 del plan de auth).

## Consecuencias

- Positivas: historial de cambios de schema versionado y auditable, rollback real ante un
  despliegue fallido, migraciones de datos (seeds) idempotentes con el mismo mecanismo.
- Negativas: más disciplina al escribir cada migración (hay que escribir el `downgrade`
  también, no solo el `upgrade`).
