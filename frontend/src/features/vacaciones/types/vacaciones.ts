/** Punto único de import de los tipos de Vacaciones — se mantiene este nombre
 * de archivo porque lo importan la mayoría de los componentes del feature; el
 * contenido se separó por dominio (§4) igual que en `insumos/types/`.
 *
 * Tipos wire del módulo — camelCase vía `serialization_alias` en los schemas
 * Pydantic (verificado contra respuestas reales del backend en el smoke del
 * checkpoint 4/5). */
export * from "./auditoria";
export * from "./ausencias";
export * from "./common";
export * from "./config";
export * from "./dashboard";
export * from "./empleados";
export * from "./feriados";
export * from "./organizacion";
export * from "./reportes";
export * from "./solicitudes";
