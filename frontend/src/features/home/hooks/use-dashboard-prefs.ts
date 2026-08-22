"use client";

import { useEffect, useRef, useState } from "react";
import { inicioPrefsApi, type InicioPrefsWire } from "../api/inicio-prefs-api";
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

function normalizar(raw: Partial<InicioPrefsWire> | Partial<DashboardPrefs> | null): DashboardPrefs {
  if (!raw) return PREFS_DEFAULT;
  const ocultos = "hiddenCards" in raw ? raw.hiddenCards : "ocultos" in raw ? raw.ocultos : [];
  const vista = "initialView" in raw ? raw.initialView : "vistaInicial" in raw ? raw.vistaInicial : "hoy";
  return {
    ocultos: Array.isArray(ocultos) ? (ocultos as CardId[]) : [],
    vistaInicial: VIEWS.some((v) => v.key === vista) ? (vista as ViewKey) : "hoy",
  };
}

function leerCache(userId: string): DashboardPrefs | null {
  try {
    const raw = window.localStorage.getItem(storageKey(userId));
    return raw ? normalizar(JSON.parse(raw) as Partial<DashboardPrefs>) : null;
  } catch {
    return null;
  }
}

function escribirCache(userId: string, prefs: DashboardPrefs): void {
  try {
    window.localStorage.setItem(storageKey(userId), JSON.stringify(prefs));
  } catch {
    // Sin storage (modo privado, bloqueo): el servidor sigue siendo la fuente.
  }
}

/** Preferencias de Inicio por CUENTA (ADR-033): el servidor
 * (`/api/me/inicio-prefs`) es la fuente de verdad y viajan entre dispositivos;
 * `localStorage` queda solo como caché para pintar al instante y como
 * respaldo si el backend no responde. Se leen después del montaje para no
 * desincronizar el SSR; `cargadas` avisa cuándo ya se puede confiar en ellas. */
export function useDashboardPrefs(userId: string) {
  const [prefs, setPrefs] = useState<DashboardPrefs>(PREFS_DEFAULT);
  const [cargadas, setCargadas] = useState(false);
  const ultimo = useRef<DashboardPrefs>(PREFS_DEFAULT);

  useEffect(() => {
    let alive = true;
    const cache = leerCache(userId);
    if (cache) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPrefs(cache);
      ultimo.current = cache;
    }
    inicioPrefsApi
      .get()
      .then((wire) => {
        if (!alive) return;
        const desdeServidor = normalizar(wire);
        ultimo.current = desdeServidor;
        setPrefs(desdeServidor);
        escribirCache(userId, desdeServidor);
      })
      .catch((err: unknown) => {
        console.error("No se pudieron leer las preferencias de Inicio; se usa la caché local.", err);
      })
      .finally(() => {
        if (alive) setCargadas(true);
      });
    return () => {
      alive = false;
    };
  }, [userId]);

  const guardar = (next: DashboardPrefs) => {
    ultimo.current = next;
    setPrefs(next);
    escribirCache(userId, next);
    inicioPrefsApi
      .put({ hiddenCards: next.ocultos, initialView: next.vistaInicial })
      .catch((err: unknown) => {
        console.error("No se pudieron guardar las preferencias de Inicio en el servidor.", err);
      });
  };

  return {
    prefs,
    cargadas,
    setOculto: (id: CardId, oculto: boolean) =>
      guardar({
        ...ultimo.current,
        ocultos: oculto
          ? [...new Set([...ultimo.current.ocultos, id])]
          : ultimo.current.ocultos.filter((c) => c !== id),
      }),
    setVistaInicial: (vistaInicial: ViewKey) => guardar({ ...ultimo.current, vistaInicial }),
    restablecer: () => guardar(PREFS_DEFAULT),
  };
}
