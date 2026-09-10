"use client";

import { useCallback, useEffect, useMemo, useRef, useSyncExternalStore } from "react";
import type { ConversacionPendiente } from "../types/wati";
import { sonarAviso } from "@/shared/utils/beep";
import { avisosStore, claveAviso } from "../utils/avisos-store";
import { nivelEspera } from "../utils/espera";
import { mostrarToastAtencion, retirarToast } from "../utils/toast-atencion";

export interface WatiAvisosState {
  /** Chats en nivel crítico (1 h) que el operador todavía no confirmó: el modal. */
  avisos: ConversacionPendiente[];
  /** Marca todos los avisos del modal como vistos (lo cierra). */
  confirmar: () => void;
}

function claveVigente(p: ConversacionPendiente): string | null {
  const nivel = nivelEspera(p.minutos_esperando);
  return nivel === "ok" ? null : claveAviso(p, nivel);
}

/** Avisos de WhatsApp para el operador de ST (ADR-036), en dos escalones:
 * a los 15 min ("atención") un toast persistente, que se da por avisado al
 * mostrarse y se retira solo cuando el chat pasa a crítico o deja de esperar;
 * a la hora ("crítico") el modal bloqueante, que queda abierto hasta que el
 * operador confirma. Las claves `wa_id:nivel` ya avisadas viven en
 * `avisosStore` (sessionStorage) y se olvidan cuando el chat deja de
 * esperar: si vuelve a esperar se avisa otra vez. Con `activo` en false no
 * se avisa nada. Suena una vez por cada chat nuevo en cualquiera de los dos
 * escalones. */
export function useWatiAvisos(
  pendientes: ConversacionPendiente[],
  activo: boolean,
  inboxUrl: string | null,
): WatiAvisosState {
  const confirmadas = useSyncExternalStore(
    avisosStore.subscribe,
    avisosStore.getSnapshot,
    avisosStore.getServerSnapshot,
  );
  const sonadas = useRef<Set<string>>(new Set());
  const toastsAbiertos = useRef<Set<string>>(new Set());

  const avisos = useMemo(() => {
    if (!activo) return [];
    return pendientes.filter((p) => {
      const k = claveVigente(p);
      return k !== null && k.endsWith(":critico") && !confirmadas.has(k);
    });
  }, [pendientes, confirmadas, activo]);

  useEffect(() => {
    const vigentes = new Set<string>();
    for (const p of pendientes) {
      const k = claveVigente(p);
      if (k) vigentes.add(k);
    }
    avisosStore.conservarSolo(vigentes);
    for (const id of [...toastsAbiertos.current]) {
      if (vigentes.has(id)) continue;
      retirarToast(id);
      toastsAbiertos.current.delete(id);
    }
  }, [pendientes]);

  useEffect(() => {
    if (!activo) return;
    const nuevas: string[] = [];
    for (const p of pendientes) {
      const k = claveVigente(p);
      if (!k || !k.endsWith(":atencion") || confirmadas.has(k)) continue;
      mostrarToastAtencion(k, p, inboxUrl);
      toastsAbiertos.current.add(k);
      nuevas.push(k);
    }
    avisosStore.confirmar(nuevas);
  }, [pendientes, confirmadas, activo, inboxUrl]);

  useEffect(() => {
    const claves = [...toastsAbiertos.current, ...avisos.map((p) => claveVigente(p) ?? "")];
    const nuevos = claves.filter((k) => !sonadas.current.has(k));
    sonadas.current = new Set(claves);
    if (nuevos.length > 0) sonarAviso();
  }, [avisos, pendientes]);

  const confirmar = useCallback(() => {
    avisosStore.confirmar(avisos.map((p) => claveVigente(p) ?? "").filter(Boolean));
  }, [avisos]);

  return { avisos, confirmar };
}
