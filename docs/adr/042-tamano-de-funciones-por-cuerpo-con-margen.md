# ADR-042: El límite de 20 líneas por función se mide sobre el cuerpo, con margen hasta 25

## Estado: Aceptado (2026-10-01)

## Contexto

`ARCHITECTURE_GUIDE.md` §4 fija 20 líneas por función. `scripts/check_sizes.py` lo medía
sobre el span físico completo (`end_lineno - lineno`), firma y docstring incluidos, y
fallaba con una sola línea de más. Al 2026-10-01:

- El inventario congelado (ADR-017/020) tenía **341 entradas**, casi todas funciones.
- Medido solo el cuerpo, las funciones de más de 20 líneas bajan de 327 a 177: casi la
  mitad de la "deuda" eran firmas largas, no funciones que hicieran demasiado. ADR-016 y
  ADR-017 ya lo habían diagnosticado ("el span físico sobreestima la complejidad"), pero
  el gate siguió midiendo igual.
- El caso típico son los endpoints FastAPI, que declaran sus dependencias en la firma
  (`Depends`, `Query`, sesión de DB, identidad). Ejemplo real: `list_puntos_mapa`
  (preventivos) medía 22, con 11 líneas de firma y 11 de lógica.
- El gate obligaba a partir funciones por 2-3 líneas (ej. `execute` de equipos por zona,
  cuerpo de 22). Eso no baja complejidad: reparte una lectura lineal en dos lugares.

## Decisión

1. **Se mide el cuerpo**: desde la primera sentencia después del docstring hasta el final.
   Firma, decoradores y docstring no cuentan.
2. **El gate falla por encima de 25 líneas de cuerpo.** El 20 de la guía sigue siendo la
   referencia al escribir; 21-25 es un margen aceptado, no un objetivo.
3. Clases (200) y archivos (300) no cambian.
4. El inventario se regeneró con el criterio nuevo **desde HEAD** (`--update` ya no mide
   el árbol de trabajo, que mezcla WIP de otras sesiones): **80 entradas** (79 funciones,
   1 archivo). Ninguna función supera las 50 líneas de cuerpo; 44 están entre 26 y 30.

## Consecuencias

- Positivas: el gate apunta a funciones largas de verdad; desaparecen los falsos
  positivos por firmas de endpoints; el inventario pasa de 341 a 80 casos, ahora sí
  accionables.
- Negativas: una función de 20 líneas de lógica con un docstring largo ya no alerta
  (aceptable: el docstring no es complejidad). Una función de 23-25 pasa sin aviso; la
  revisión sigue pudiendo pedir dividirla si mezcla responsabilidades.
- La guía (§4, "Cómo se mide en este repo") remite a esta ADR.
