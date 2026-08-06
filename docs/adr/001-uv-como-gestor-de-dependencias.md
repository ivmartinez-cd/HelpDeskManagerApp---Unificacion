# ADR-001: uv + uv.lock como gestor de dependencias del backend

## Estado: Aceptado

## Contexto

`ARCHITECTURE_GUIDE.md` §5 exige versiones fijadas en producción. El repo padre
(`HelpDeskManager-Web/backend/requirements.txt`) tiene 0 de 23 dependencias pineadas y no
fija el árbol transitivo — dos instalaciones del mismo `requirements.txt` en momentos
distintos pueden traer versiones distintas de una dependencia indirecta.

## Decisión

Usamos `uv` con `pyproject.toml` + `uv.lock` commiteado. `uv` ya está instalado y validado
en el entorno de desarrollo (Fase 1 de `INTEGRACION_APPS_PLAN.md`).

## Consecuencias

- Positivas: `uv.lock` fija versión **y hash** de todo el árbol transitivo, no solo las
  dependencias directas. `uv sync --frozen` falla si el lock no coincide con el
  `pyproject.toml`, evitando derivas silenciosas. Instalación reproducible en CI, Docker y
  local con el mismo comando.
- Negativas: una herramienta más que el equipo tiene que conocer (mitigado: la CLI es
  compatible en espíritu con `pip`).
