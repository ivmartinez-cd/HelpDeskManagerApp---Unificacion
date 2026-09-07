"use client";

import { useCallback, useEffect, useMemo, useRef, useSyncExternalStore } from "react";
import type { ConversacionPendiente } from "../types/wati";
import { avisosStore, claveAviso } from "../utils/avisos-store";
import { sonarAviso } from "../utils/beep";
import { nivelEspera } from "../utils/espera";

export interface WatiAvisosState {
  /** Chats que cruzaron un umbral de espera y el operador todavía no confirmó. */
  avisos: ConversacionPendiente[];
  /** Marca todos los avisos abiertos como vistos (cierra el modal). */
  confirmar: () => void;
}

function claveVigente(p: ConversacionPendiente): string | null {
  const nivel = nivelEspera(p.minutos_esperando);
  return nivel === "ok" ? null : claveAviso(p, nivel);
}

/** Avisos de WhatsApp para el operador de ST: un chat entra a la lista al
 * llegar a "atención" y de nuevo al llegar a "crítico", y sale cuando el
 * operador lo confirma (o cuando deja de estar pendiente). Las confirmaciones
 * viven en `avisosStore` (sessionStorage), así que sobreviven una recarga,
 * y se olvidan cuando el chat deja de esperar: si vuelve a esperar se avisa
 * otra vez. Con `activo` en false no se avisa nada (el usuario no es quien
 * cubre ST ahora), pero las confirmaciones se conservan. Suena una vez por
 * cada chat nuevo en la lista. */
export function useWatiAvisos(pendientes: ConversacionPendiente[], activo: boolean): WatiAvisosState {
  const confirmadas = useSyncExternalStore(
    avisosStore.subscribe,
    avisosStore.getSnapshot,
    avisosStore.getServerSnapshot,
  );
  const sonadas = useRef<Set<string>>(new Set());

  const avisos = useMemo(() => {
    if (!activo) return [];
    return pendientes.filter((p) => {
      const k = claveVigente(p);
      return k !== null && !confirmadas.has(k);
    });
  }, [pendientes, confirmadas, activo]);

  useEffect(() => {
    const vigentes = new Set<string>();
    for (const p of pendientes) {
      const k = claveVigente(p);
      if (k) vigentes.add(k);
    }
    avisosStore.conservarSolo(vigentes);
  }, [pendientes]);

  useEffect(() => {
    const claves = avisos.map((p) => claveVigente(p) ?? "");
    const nuevos = claves.filter((k) => !sonadas.current.has(k));
    sonadas.current = new Set(claves);
    if (nuevos.length > 0) sonarAviso();
  }, [avisos]);

  const confirmar = useCallback(() => {
    avisosStore.confirmar(avisos.map((p) => claveVigente(p) ?? "").filter(Boolean));
  }, [avisos]);

  return { avisos, confirmar };
}
