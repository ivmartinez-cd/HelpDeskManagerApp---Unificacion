"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import type { Alerta } from "../types/liquidaciones";

const ESTADOS_ABIERTOS: ReadonlySet<string> = new Set(["pendiente", "en_revision"]);

/** Alertas que todavía se pueden gestionar (pendientes o en revisión). */
export function alertasAbiertas(alertas: Alerta[]): Alerta[] {
  return alertas.filter((a) => ESTADOS_ABIERTOS.has(a.estado));
}

/** Selección múltiple de incidentes para gestionar sus alertas en lote
 * (2026-09-03): tildar un incidente selecciona todas sus alertas abiertas. El
 * estado vive arriba de las secciones Correctivos/Preventivos para que una
 * sola barra de acciones cubra toda la liquidación (caso típico: toda la
 * liquidación de una zona con costo doble, mismo motivo para todas). */
interface SeleccionAlertas {
  /** Ids de incidentes tildados. */
  seleccionados: ReadonlySet<string>;
  /** Alertas abiertas de los incidentes tildados — lo que se manda al backend. */
  alertasSeleccionadas: Alerta[];
  esSeleccionable: (incidenteId: string) => boolean;
  toggle: (incidenteId: string) => void;
  seleccionarTodos: (incidenteIds: string[], tildar: boolean) => void;
  limpiar: () => void;
}

const SeleccionAlertasContext = createContext<SeleccionAlertas | null>(null);

export function SeleccionAlertasProvider({
  alertasByInc,
  children,
}: {
  alertasByInc: Record<string, Alerta[]>;
  children: ReactNode;
}) {
  const [seleccionados, setSeleccionados] = useState<ReadonlySet<string>>(new Set());

  const esSeleccionable = useCallback(
    (incidenteId: string) => alertasAbiertas(alertasByInc[incidenteId] ?? []).length > 0,
    [alertasByInc],
  );

  const toggle = useCallback((incidenteId: string) => {
    setSeleccionados((prev) => {
      const next = new Set(prev);
      if (next.has(incidenteId)) next.delete(incidenteId);
      else next.add(incidenteId);
      return next;
    });
  }, []);

  const seleccionarTodos = useCallback((incidenteIds: string[], tildar: boolean) => {
    setSeleccionados((prev) => {
      const next = new Set(prev);
      for (const id of incidenteIds) {
        if (tildar) next.add(id);
        else next.delete(id);
      }
      return next;
    });
  }, []);

  const limpiar = useCallback(() => setSeleccionados(new Set()), []);

  // Se recalcula sobre `alertasByInc` fresco: si tras un `load()` una alerta
  // tildada ya no está abierta, deja de contar sin tocar la selección.
  const alertasSeleccionadas = useMemo(
    () =>
      Array.from(seleccionados).flatMap((incId) => alertasAbiertas(alertasByInc[incId] ?? [])),
    [seleccionados, alertasByInc],
  );

  const value = useMemo<SeleccionAlertas>(
    () => ({ seleccionados, alertasSeleccionadas, esSeleccionable, toggle, seleccionarTodos, limpiar }),
    [seleccionados, alertasSeleccionadas, esSeleccionable, toggle, seleccionarTodos, limpiar],
  );

  return (
    <SeleccionAlertasContext.Provider value={value}>{children}</SeleccionAlertasContext.Provider>
  );
}

/** `null` fuera del provider: la tabla de incidentes se renderiza igual, sin tildes. */
export function useSeleccionAlertas(): SeleccionAlertas | null {
  return useContext(SeleccionAlertasContext);
}
