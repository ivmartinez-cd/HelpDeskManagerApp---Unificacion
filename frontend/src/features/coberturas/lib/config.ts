import { coberturasContadoresApi, coberturasPstApi, coberturasTurnosApi } from "../api/coberturas-api";
import type { CoberturaEntityType, CoberturasApi } from "../types/coberturas";

/** Textos y cableado por módulo. El handoff original planteaba la variante
 * PST como "un PST cubre a otro PST", pero el dominio real (ADR-013) es
 * otro: en ambos módulos el que falta y el que cubre son OPERADORES — lo
 * que cambia es el alcance (clientes de Gestión en contadores, PST del
 * catálogo en prestadores). Los labels se adaptaron a eso; el resto del
 * diseño (tabla, badges, modal) sigue el handoff tal cual. */
export interface CoberturaConfig {
  api: CoberturasApi;
  subtitulo: string;
  /** unidad del alcance parcial, para la columna ("3 clientes" / "3 PST") */
  alcanceUnidad: string;
  /** singular de `alcanceUnidad` con artículo, para el mensaje de validación
   * ("Seleccioná al menos ___") -- antes hardcodeado como ternario
   * PST/cliente en el modal, lo que rompía con un tercer módulo. */
  alcanceItemSingular: string;
  alcanceTotalHint: string;
  alcanceParcialLabel: string;
  multiLabel: string;
  multiPlaceholder: string;
  /** true = el alcance no tiene catálogo y se cargan valores a mano */
  multiAllowCustom: boolean;
  footerCopy: string;
  notaVuelta: (hasta: string, ausente: string) => string;
  permisoCrear: { moduleKey: string; actionKey: string };
  /** Editar y cancelar — misma acción de backend (update/manage). */
  permisoMutar: { moduleKey: string; actionKey: string };
}

export const COBERTURA_CONFIG: Record<CoberturaEntityType, CoberturaConfig> = {
  contador: {
    api: coberturasContadoresApi,
    subtitulo: "Contadores / Operadores",
    alcanceUnidad: "clientes",
    alcanceItemSingular: "un cliente",
    alcanceTotalHint: "Todos los clientes del operador",
    alcanceParcialLabel: "Clientes específicos",
    multiLabel: "Clientes o sucursales",
    multiPlaceholder: "Escribí el cliente tal como figura en el Calendario…",
    multiAllowCustom: true,
    footerCopy:
      "Al vencer la vigencia, los clientes vuelven automáticamente a su operador original. Las coberturas no modifican el Calendario de Gestión.",
    notaVuelta: (hasta, ausente) =>
      `Esta cobertura es temporal y no modifica el Calendario de Gestión. Al finalizar el ${hasta}, los clientes vuelven a ${ausente} automáticamente.`,
    permisoCrear: { moduleKey: "contadores", actionKey: "manage" },
    permisoMutar: { moduleKey: "contadores", actionKey: "manage" },
  },
  pst: {
    api: coberturasPstApi,
    subtitulo: "Prestadores / PST",
    alcanceUnidad: "PST",
    alcanceItemSingular: "un PST",
    alcanceTotalHint: "Todos los PST del operador",
    alcanceParcialLabel: "PST específicos",
    multiLabel: "Prestadores (PST)",
    multiPlaceholder: "Buscá un PST…",
    multiAllowCustom: false,
    footerCopy:
      "Al vencer la vigencia, los PST vuelven automáticamente a su operador original. Las coberturas no modifican la asignación permanente ni su historial.",
    notaVuelta: (hasta, ausente) =>
      `Esta cobertura es temporal y no modifica la asignación permanente. Al finalizar el ${hasta}, los PST vuelven a ${ausente} automáticamente.`,
    permisoCrear: { moduleKey: "prestadores", actionKey: "create" },
    permisoMutar: { moduleKey: "prestadores", actionKey: "update" },
  },
  turno: {
    api: coberturasTurnosApi,
    subtitulo: "Turnos / Operadores",
    alcanceUnidad: "franjas",
    alcanceItemSingular: "una franja",
    alcanceTotalHint: "Todas las franjas del operador",
    alcanceParcialLabel: "Franjas específicas",
    multiLabel: "Franjas horarias",
    multiPlaceholder: "Buscá una franja…",
    multiAllowCustom: false,
    footerCopy:
      "Al vencer la vigencia, las franjas vuelven automáticamente a su operador original. Las coberturas no modifican la Configuración de Turnos ni su historial. Para re-cortar horarios o crear/eliminar franjas durante una ausencia, usá el Modo vacaciones.",
    notaVuelta: (hasta, ausente) =>
      `Esta cobertura es temporal y no modifica la Configuración de Turnos. Al finalizar el ${hasta}, las franjas vuelven a ${ausente} automáticamente.`,
    permisoCrear: { moduleKey: "admin", actionKey: "manage" },
    permisoMutar: { moduleKey: "admin", actionKey: "manage" },
  },
};
