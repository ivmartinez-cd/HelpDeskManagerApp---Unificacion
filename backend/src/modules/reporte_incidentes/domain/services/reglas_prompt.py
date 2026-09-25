"""Reglas de tipificación que van en el prompt (port literal de `TAXONOMY_RULES_V1`,
`taxonomy.v1.ts`, versión v1.6-2026-06-24). Copiado tal cual del legacy: cambiar una
coma cambia cómo tipifica la IA, y la caché importada se generó con este texto."""

REGLAS_V1 = """
JERARQUIA DE EVALUACION (en orden):
1. SENAL PRIMARIA = la SOLUCION (lo que el tecnico efectivamente hizo al cerrar).
2. DESEMPATE: si la solucion abarca dos categorias, gana la que RESUELVE la queja
   original del cliente (campos "Fallas:" y "Observaciones:" de la descripcion).
3. CAUSA = ignorar (es ruido: 78% es "EQ-Equipo"/"Indeterminado"). Usar SOLO como
   pista muy debil si la solucion esta vacia.
4. MESA DE AYUDA / SIN RESPUESTA => "Gestion de Soporte" > "Mesa de ayuda / Sin
   respuesta del cliente" cuando el caso lo toma la mesa de ayuda, se consulta al
   cliente (mail/bitacora/whatsapp/llamada) y NO hubo accion tecnica real ni
   respuesta del cliente (incluye troquelado SOLO sospechado, sin confirmar). OJO:
   si el tecnico HIZO algo (configuro, cambio, reparo) y ADEMAS cerro esperando
   confirmacion, vale el TRABAJO realizado, no la espera.
   - Si el cliente RESPONDE que lo resolvio solo => "Instructivo / Autoresolucion".

REGLAS ESPECIFICAS:
- LIMPIEZA / MANTENIMIENTO GENERAL SIN reemplazo de pieza => NO es Hardware. Va a
  "Medio de Impresion" si el sintoma fue atasco, o a la categoria del sintoma real.
  "Hardware y Desgaste" SOLO si hubo REEMPLAZO o REPARACION de pieza por desgaste/
  rotura (fusor, rodillos pickup/retard/separacion, kit mantenimiento, panel/botonera,
  cover, fuente).
- PAPEL ESPECIAL / TROQUELADO: el problema NO es que el papel sea troquelado en si,
  sino que (sobre todo en Dia) el troquelado viene MAL CORTADO / mal troquelado /
  humedo y genera tanto ATASCOS como problemas de CONFIGURACION (escala/orientacion/
  tamano). Todo eso => "Papel especial / Troquelado", AUNQUE la solucion mencione
  limpieza, rodillos o reconfiguracion (el problema de fondo es el medio).
- PAPEL INADECUADO: papel humedo / de mala calidad / resma inadecuada / gramaje
  equivocado que NO es troquelado => "Papel inadecuado / humedad / mala calidad".
- PROBLEMA EXTERNO: si la falla es de la infra del cliente y NO del equipo (boca de
  red rota, cable de red del sitio, red caida, certificados/permisos de terceros,
  corte de luz) y el equipo esta OK => "Gestion de Soporte" > "Problema externo /
  Red del cliente".
- CONFIGURACION/ASISTENCIA AL USUARIO con equipo OK (se explico como configurar,
  red, driver) => "Software, Firmware y Red" (o "Gestion de Soporte" si fue solo
  instructivo/autoresolucion sin tocar el equipo).
- ESCANER / ADF (vidrio/platina, alimentador ADF, rodillos de ADF, calibracion de
  escaneo, escaner bloqueado, reset/config del escaner) => SIEMPRE "Hardware y
  Desgaste" > "Escaner / ADF", sea limpieza, config, reset admin o reemplazo de
  pieza. Es un dominio propio. NUNCA a Software ni a Diagnostico por ser escaner.
- LIMPIEZA / REUBICACION / LUBRICACION SIN reemplazar pieza (ej. "se coloca/reubica
  pickup", "lubricacion de modulo", "se limpia rodillo") para destrabar un atasco =>
  va al SINTOMA (Medio de Impresion > Atasco), NO a Hardware. Hardware solo si se
  REEMPLAZO/REPARO una pieza.
- TOLVA / CONTENEDOR RESIDUAL de toner (vaciar/lavar tolva, botella/contenedor
  residual, "sustituya unidad de recogida de toner") => "Insumos y Toner" >
  "Tolva / Contenedor residual" (NO "Toner / Cartucho" ni "Otros").
- CABLE DE RED / CONECTIVIDAD que arregla el tecnico (cambia cable de red, configura
  IP, instala certificados) => "Software, Firmware y Red" (Config red / IP), aunque
  el cable sea del sitio. "Problema externo / Red del cliente" SOLO si el problema
  queda en la infra del cliente y NO se resolvio desde el equipo.
- DIAGNOSTICO SIN FALLA: si el tecnico reviso/testeo y el equipo quedo OK SIN
  reparar ni reemplazar nada (no se reprodujo/encontro la falla) => "Gestion de
  Soporte" > "Diagnostico / Sin falla".
- DRUM / UNIDAD DE IMAGEN / REVELADOR (developer): consumibles tecnicos =>
  "Insumos y Toner" > "Drum / Unidad de imagen / Revelador" (NO Hardware).
- MANTENIMIENTO PREVENTIVO: limpieza general / reset de contadores / "service" SIN
  falla puntual ni reemplazo de pieza => "Gestion de Soporte" > "Mantenimiento /
  Limpieza general". OJO: si la limpieza fue para RESOLVER un sintoma concreto
  (ej. limpiar para destrabar un atasco), va a la categoria del sintoma (Medio).
- CALIBRACION / AJUSTE DE IMAGEN (imagen corrida, registro, alineacion) =>
  "Software, Firmware y Red" > "Calibracion / Ajuste de imagen".
- REPARAR/CAMBIAR una parte del FUSOR (una de detack, bujes, rodillo de fusor,
  hot roll) => "Hardware y Desgaste" > "Fusor / Kit de mantenimiento".
- CONFIGURAR (red/IP/bandejas/tipo o tamano de papel/driver), AUNQUE sea guiando
  al usuario en remoto => "Software, Firmware y Red" (Config red/IP o Driver/PC),
  NO "Instructivo / Autoresolucion". Instructivo/Autoresolucion SOLO si NO se toco
  ninguna config tecnica y el cliente lo resolvio por su cuenta.
- AJUSTE/RECONFIGURACION de bandejas hecho para DESTRABAR un atasco => "Medio de
  Impresion" > "Atasco de papel (comun)". Usar "Ajuste de bandejas / guias" SOLO
  cuando el ajuste de la guia/bandeja ES la solucion central (no un atasco).

CONFIANZA:
- Elegi SIEMPRE la subcategoria ESPECIFICA que mejor aplique. Usa "Otros - <cat>"
  SOLO si NINGUNA subcategoria especifica de esa categoria aplica de verdad.
- Si ni la categoria esta clara => marcar PENDIENTE (no inventar).
""".strip()
