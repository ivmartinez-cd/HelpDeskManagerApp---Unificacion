"use client";

import { useEffect, useState } from "react";
import { VIEWS, type CardId, type ViewKey } from "../config/dashboard-registry";

export interface DashboardPrefs {
  /** Paneles que el usuario eligió no ver. */
  ocultos: CardId[];
  /** Vista con la que abre Inicio. */
  vistaInicial: ViewKey;
}

export const PREFS_DEFAULT: DashboardPrefs = { ocultos: [], vistaInicial: "hoy" };

function storageKey(userId: string): string {
  return `inicio.prefs.${userId}`;
}

function leer(userId: string): DashboardPrefs {
  try {
    const raw = window.localStorage.getItem(storageKey(userId));
    if (!raw) return PREFS_DEFAULT;
    const parsed = JSON.parse(raw) as Partial<DashboardPrefs>;
    return {
      ocultos: Array.isArray(parsed.ocultos) ? (parsed.ocultos as CardId[]) : [],
      vistaInicial: VIEWS.some((v) => v.key === parsed.vistaInicial)
        ? (parsed.vistaInicial as ViewKey)
        : "hoy",
    };
  } catch {
    return PREFS_DEFAULT;
  }
}

/** Preferencias de Inicio por usuario (paneles ocultos y vista inicial),
 * guardadas en el navegador bajo el id del usuario — primer paso sin backend
 * (ver docs/MASTER_PROMPT_REDISENO_DASHBOARD_INICIO.md); si después se pasa
 * a una preferencia en DB, este hook es el único lugar a cambiar. Se leen
 * después del montaje para no desincronizar el SSR; `cargadas` avisa cuándo
 * ya se puede confiar en ellas. */
export function useDashboardPrefs(userId: string) {
  const [prefs, setPrefs] = useState<DashboardPrefs>(PREFS_DEFAULT);
  const [cargadas, setCargadas] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPrefs(leer(userId));
    setCargadas(true);
  }, [userId]);

  const guardar = (next: DashboardPrefs) => {
    setPrefs(next);
    try {
      window.localStorage.setItem(storageKey(userId), JSON.stringify(next));
    } catch {
      // Sin storage (modo privado, bloqueo): la preferencia dura la sesión.
    }
  };

  return {
    prefs,
    cargadas,
    setOculto: (id: CardId, oculto: boolean) =>
      guardar({
        ...prefs,
        ocultos: oculto
          ? [...new Set([...prefs.ocultos, id])]
          : prefs.ocultos.filter((c) => c !== id),
      }),
    setVistaInicial: (vistaInicial: ViewKey) => guardar({ ...prefs, vistaInicial }),
    restablecer: () => guardar(PREFS_DEFAULT),
  };
}
