/** Shape normalizado de la UI de Coberturas (overrides temporales de
 * asignación, ADR-013). Los dos backends exponen el mismo concepto con
 * contratos distintos — contadores serializa snake_case y usa usernames de
 * Gestión como id de operador; prestadores serializa camelCase y usa UUIDs
 * de app_user. Los adapters de `api/coberturas-api.ts` normalizan ambos a
 * este shape para que los componentes sean un único código parametrizado
 * (`entityType`), como pide el handoff. */

export type CoberturaEntityType = "contador" | "pst" | "turno";

/** Estado persistido en DB (ADR-013): solo ACTIVA/CANCELADA. Los estados
 * visibles Programada/Vencida se derivan por fecha en `lib/estado.ts`. */
export type CoberturaEstadoDb = "ACTIVA" | "CANCELADA";

export type CoberturaEstadoUi = "activa" | "programada" | "vencida" | "cancelada";

export interface Cobertura {
  id: string;
  ausenteId: string;
  ausenteNombre: string | null;
  reemplazanteId: string;
  reemplazanteNombre: string | null;
  /** ISO YYYY-MM-DD (fecha pura, sin hora) */
  desde: string;
  hasta: string;
  alcanceTotal: boolean;
  /** Clientes (texto libre de Gestión) en contadores; ids de prestador en pst */
  alcanceItems: string[];
  estado: CoberturaEstadoDb;
  motivo: string | null;
  /** Par de coberturas cruzadas al que pertenece (intercambio de turnos,
   * ADR-026); null en una cobertura común. Solo turnos lo expone. */
  intercambioId: string | null;
}

/** Intercambio de turnos (ADR-026): dos coberturas cruzadas con el mismo
 * `intercambioId`. `ida` = A ausente → B cubre (franjas de A); `vuelta` = B
 * ausente → A cubre (franjas de B). Se arma en el cliente agrupando el
 * listado plano (`lib/intercambios.ts`). */
export interface Intercambio {
  id: string;
  ida: Cobertura;
  vuelta: Cobertura;
}

/** Fila de la tabla: una cobertura común o un intercambio (una sola fila). */
export type FilaCoberturas =
  | { tipo: "cobertura"; cobertura: Cobertura }
  | { tipo: "intercambio"; intercambio: Intercambio };

export interface IntercambioPayload {
  operadorAId: string;
  operadorBId: string;
  desde: string;
  hasta: string;
  /** franjas de A que pasa a cubrir B; null = todas */
  alcanceItemsA: string[] | null;
  /** franjas de B que pasa a cubrir A; null = todas */
  alcanceItemsB: string[] | null;
  motivo: string | null;
}

/** Endpoints del par (solo turnos): el alta/edición devuelven las dos
 * coberturas, pero la vista recarga el listado igual, así que acá basta
 * con resolver. */
export interface IntercambiosApi {
  create: (payload: IntercambioPayload) => Promise<void>;
  update: (id: string, payload: IntercambioPayload) => Promise<void>;
  cancel: (id: string) => Promise<void>;
}

export interface CreateCoberturaPayload {
  ausenteId: string;
  reemplazanteId: string;
  desde: string;
  hasta: string;
  /** null = alcance total */
  alcanceItems: string[] | null;
  motivo: string | null;
}

export interface CoberturaOperadorOption {
  id: string;
  nombre: string;
  /** ej. "@vipaez" en contadores; sin sublabel en prestadores */
  sublabel?: string;
  color: string | null;
}

export interface AlcanceOption {
  id: string;
  label: string;
}

/** Contrato que cada módulo implementa en `api/coberturas-api.ts`. */
export interface CoberturasApi {
  list: () => Promise<Cobertura[]>;
  create: (payload: CreateCoberturaPayload) => Promise<Cobertura>;
  /** Edición in-place de una cobertura activa/programada (mismo id, mismo
   * body que el alta — ADR-013, actualización 2026-08-14). */
  update: (id: string, payload: CreateCoberturaPayload) => Promise<Cobertura>;
  cancel: (id: string) => Promise<void>;
  listOperadores: () => Promise<CoberturaOperadorOption[]>;
  /** Catálogo para el multi-select de alcance parcial. Vacío en contadores:
   * los clientes de Gestión no tienen catálogo propio (texto libre en los
   * eventos), se cargan a mano en el select (allowCustom). */
  listAlcanceOptions: () => Promise<AlcanceOption[]>;
}
