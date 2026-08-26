import { httpClient } from "@/services/http-client";
import type {
  AlcanceOption,
  Cobertura,
  CoberturasApi,
  CreateCoberturaPayload,
} from "../types/coberturas";

import type { Page } from "@/shared/types/pagination";

// ── Contadores — wire snake_case (schemas sin serialization_alias) ──────────

/** Nombres tal como los serializa `AsignacionOverrideResponse` de
 * `contadores/presentation/schemas/calendario_schemas.py` (from_attributes,
 * sin alias camelCase — verificado contra el schema real). */
interface ContadoresOverrideWire {
  id: string;
  operador_ausente_id: string;
  operador_ausente_nombre: string | null;
  operador_reemplazante_id: string;
  operador_reemplazante_nombre: string | null;
  vigente_desde: string;
  vigente_hasta: string;
  alcance_total: boolean;
  clientes: string[];
  estado: "ACTIVA" | "CANCELADA";
  motivo: string | null;
}

function fromContadoresWire(w: ContadoresOverrideWire): Cobertura {
  return {
    id: w.id,
    ausenteId: w.operador_ausente_id,
    ausenteNombre: w.operador_ausente_nombre,
    reemplazanteId: w.operador_reemplazante_id,
    reemplazanteNombre: w.operador_reemplazante_nombre,
    desde: w.vigente_desde,
    hasta: w.vigente_hasta,
    alcanceTotal: w.alcance_total,
    alcanceItems: w.clientes,
    estado: w.estado,
    motivo: w.motivo,
    intercambioId: null,
  };
}

export const coberturasContadoresApi: CoberturasApi = {
  list: () =>
    httpClient
      .get<Page<ContadoresOverrideWire>>("/api/contadores/calendario/overrides")
      .then((p) => p.items.map(fromContadoresWire)),

  create: (payload: CreateCoberturaPayload) =>
    httpClient
      .post<ContadoresOverrideWire>("/api/contadores/calendario/overrides", {
        operador_ausente_id: payload.ausenteId,
        operador_reemplazante_id: payload.reemplazanteId,
        vigente_desde: payload.desde,
        vigente_hasta: payload.hasta,
        clientes: payload.alcanceItems,
        motivo: payload.motivo,
      })
      .then(fromContadoresWire),

  update: (id: string, payload: CreateCoberturaPayload) =>
    httpClient
      .put<ContadoresOverrideWire>(`/api/contadores/calendario/overrides/${id}`, {
        operador_ausente_id: payload.ausenteId,
        operador_reemplazante_id: payload.reemplazanteId,
        vigente_desde: payload.desde,
        vigente_hasta: payload.hasta,
        clientes: payload.alcanceItems,
        motivo: payload.motivo,
      })
      .then(fromContadoresWire),

  cancel: (id: string) =>
    httpClient.post<void>(`/api/contadores/calendario/overrides/${id}/cancelar`),

  listOperadores: () =>
    httpClient
      .get<Page<{ id: string; nombre: string; color: string | null }>>(
        "/api/contadores/calendario/operadores",
      )
      .then((p) =>
        p.items.map((o) => ({
          id: o.id,
          nombre: o.nombre,
          sublabel: `@${o.id}`,
          color: o.color,
        })),
      ),

  // Los clientes de Gestión son texto libre en los eventos, sin catálogo
  // consultable — el multi-select trabaja con entradas manuales (allowCustom).
  listAlcanceOptions: () => Promise.resolve([]),
};

// ── Prestadores — wire camelCase (serialization_alias en los schemas) ───────

/** Nombres tal como los serializa `AsignacionOverrideResponse` de
 * `prestadores/presentation/schemas/prestador_schemas.py` (camelCase vía
 * serialization_alias — verificado contra el schema real). */
interface PrestadoresOverrideWire {
  id: string;
  operadorAusenteId: string;
  operadorAusenteNombre: string | null;
  operadorReemplazanteId: string;
  operadorReemplazanteNombre: string | null;
  desde: string;
  hasta: string;
  alcanceTotal: boolean;
  prestadorIds: string[];
  estado: "ACTIVA" | "CANCELADA";
  motivo: string | null;
}

function fromPrestadoresWire(w: PrestadoresOverrideWire): Cobertura {
  return {
    id: w.id,
    ausenteId: w.operadorAusenteId,
    ausenteNombre: w.operadorAusenteNombre,
    reemplazanteId: w.operadorReemplazanteId,
    reemplazanteNombre: w.operadorReemplazanteNombre,
    desde: w.desde,
    hasta: w.hasta,
    alcanceTotal: w.alcanceTotal,
    alcanceItems: w.prestadorIds,
    estado: w.estado,
    motivo: w.motivo,
    intercambioId: null,
  };
}

interface PrestadorResumenWire {
  grupos: { prestadores: { id: string; denComercial: string }[] }[];
}

export const coberturasPstApi: CoberturasApi = {
  list: () =>
    httpClient
      .get<Page<PrestadoresOverrideWire>>("/api/prestadores/overrides")
      .then((p) => p.items.map(fromPrestadoresWire)),

  create: (payload: CreateCoberturaPayload) =>
    httpClient
      .post<PrestadoresOverrideWire>("/api/prestadores/overrides", {
        operadorAusenteId: payload.ausenteId,
        operadorReemplazanteId: payload.reemplazanteId,
        desde: payload.desde,
        hasta: payload.hasta,
        prestadorIds: payload.alcanceItems,
        motivo: payload.motivo,
      })
      .then(fromPrestadoresWire),

  update: (id: string, payload: CreateCoberturaPayload) =>
    httpClient
      .put<PrestadoresOverrideWire>(`/api/prestadores/overrides/${id}`, {
        operadorAusenteId: payload.ausenteId,
        operadorReemplazanteId: payload.reemplazanteId,
        desde: payload.desde,
        hasta: payload.hasta,
        prestadorIds: payload.alcanceItems,
        motivo: payload.motivo,
      })
      .then(fromPrestadoresWire),

  cancel: (id: string) => httpClient.post<void>(`/api/prestadores/overrides/${id}/cancelar`),

  listOperadores: () =>
    httpClient
      .get<Page<{ id: string; fullName: string; color: string | null }>>(
        "/api/prestadores/operadores",
      )
      .then((p) => p.items.map((o) => ({ id: o.id, nombre: o.fullName, color: o.color }))),

  listAlcanceOptions: () =>
    httpClient
      .get<PrestadorResumenWire>("/api/prestadores")
      .then((r): AlcanceOption[] =>
        r.grupos.flatMap((g) =>
          g.prestadores.map((p) => ({ id: p.id, label: p.denComercial })),
        ),
      ),
};

// ── Turnos — wire camelCase (serialization_alias en los schemas) ───────────

/** Nombres tal como los serializa `AsignacionOverrideResponse` de
 * `turnos/presentation/schemas/turno_schemas.py` (camelCase vía
 * serialization_alias, mismo criterio que prestadores). */
interface TurnosOverrideWire {
  id: string;
  operadorAusenteId: string;
  operadorAusenteNombre: string | null;
  operadorReemplazanteId: string;
  operadorReemplazanteNombre: string | null;
  desde: string;
  hasta: string;
  alcanceTotal: boolean;
  slotIds: string[];
  estado: "ACTIVA" | "CANCELADA";
  motivo: string | null;
  /** ADR-026: par de coberturas cruzadas (intercambio); null en una común. */
  intercambioId: string | null;
}

function fromTurnosWire(w: TurnosOverrideWire): Cobertura {
  return {
    id: w.id,
    ausenteId: w.operadorAusenteId,
    ausenteNombre: w.operadorAusenteNombre,
    reemplazanteId: w.operadorReemplazanteId,
    reemplazanteNombre: w.operadorReemplazanteNombre,
    desde: w.desde,
    hasta: w.hasta,
    alcanceTotal: w.alcanceTotal,
    alcanceItems: w.slotIds,
    estado: w.estado,
    motivo: w.motivo,
    intercambioId: w.intercambioId ?? null,
  };
}

const DIAS_SEMANA_ABREV = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

interface TurnosCasillaWire {
  id: string;
  nombre: string;
}

interface TurnosSlotWire {
  id: string;
  casillaId: string;
  horaInicio: string;
  horaFin: string;
  diaSemana: number;
}

export const coberturasTurnosApi: CoberturasApi = {
  list: () =>
    httpClient.get<Page<TurnosOverrideWire>>("/api/turnos/overrides").then((p) =>
      p.items.map(fromTurnosWire),
    ),

  create: (payload: CreateCoberturaPayload) =>
    httpClient
      .post<TurnosOverrideWire>("/api/turnos/overrides", {
        operadorAusenteId: payload.ausenteId,
        operadorReemplazanteId: payload.reemplazanteId,
        desde: payload.desde,
        hasta: payload.hasta,
        slotIds: payload.alcanceItems,
        motivo: payload.motivo,
      })
      .then(fromTurnosWire),

  update: (id: string, payload: CreateCoberturaPayload) =>
    httpClient
      .put<TurnosOverrideWire>(`/api/turnos/overrides/${id}`, {
        operadorAusenteId: payload.ausenteId,
        operadorReemplazanteId: payload.reemplazanteId,
        desde: payload.desde,
        hasta: payload.hasta,
        slotIds: payload.alcanceItems,
        motivo: payload.motivo,
      })
      .then(fromTurnosWire),

  cancel: (id: string) => httpClient.post<void>(`/api/turnos/overrides/${id}/cancelar`),

  listOperadores: () =>
    httpClient
      .get<Page<{ id: string; fullName: string; color: string | null }>>("/api/turnos/users")
      .then((p) => p.items.map((o) => ({ id: o.id, nombre: o.fullName, color: o.color }))),

  // Alcance parcial = franjas concretas (slot). El label compuesto necesita
  // el nombre de casilla, que no viaja en /slots -- se arma con /casillas.
  listAlcanceOptions: () =>
    Promise.all([
      httpClient.get<Page<TurnosCasillaWire>>("/api/turnos/casillas"),
      httpClient.get<Page<TurnosSlotWire>>("/api/turnos/slots"),
    ]).then(([casillasPage, slotsPage]): AlcanceOption[] => {
      const casillaNombrePorId = new Map(
        casillasPage.items.map((c) => [c.id, c.nombre] as const),
      );
      return slotsPage.items.map((s) => ({
        id: s.id,
        label: `${casillaNombrePorId.get(s.casillaId) ?? "?"} · ${
          DIAS_SEMANA_ABREV[s.diaSemana] ?? "?"
        } ${s.horaInicio.slice(0, 5)}-${s.horaFin.slice(0, 5)}`,
      }));
    }),
};
