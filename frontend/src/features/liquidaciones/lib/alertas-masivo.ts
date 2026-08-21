import { CODIGO_ALT009, TRANSICIONES_ALERTA } from "./alerta-estados";
import type { Alerta, EstadoAlerta } from "../types/liquidaciones";

/** ALT009 pendiente/en_revision no tiene transición directa a "en_revision" ni
 * "resuelta": el click abre el wizard para cargar la sucursal faltante en Tabla
 * KM (ver `AlertaRow.onResolverAlt009`). Una acción masiva no puede completar
 * ese wizard por cada alerta, así que se excluye de esos dos destinos. */
function esTransicionDirecta(alerta: Alerta, estadoDestino: EstadoAlerta): boolean {
  if (estadoDestino !== "en_revision" && estadoDestino !== "resuelta") return true;
  const requiereWizard =
    alerta.tipoAlerta === CODIGO_ALT009 &&
    (alerta.estado === "pendiente" || alerta.estado === "en_revision");
  return !requiereWizard;
}

function puedeTransicionar(alerta: Alerta, estadoDestino: EstadoAlerta): boolean {
  return (TRANSICIONES_ALERTA[alerta.estado] ?? []).some((t) => t.estado === estadoDestino);
}

/** Subconjunto de `alertas` al que se le puede aplicar `estadoDestino` de
 * forma masiva (sin abrir un modal por alerta individual). */
export function elegiblesParaEstadoMasivo(alertas: Alerta[], estadoDestino: EstadoAlerta): Alerta[] {
  return alertas.filter((a) => puedeTransicionar(a, estadoDestino) && esTransicionDirecta(a, estadoDestino));
}
