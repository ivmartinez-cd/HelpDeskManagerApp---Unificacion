"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import type { ConversacionPendiente } from "../types/wati";
import { sonarAviso } from "../utils/beep";
import { nivelEspera, textoEspera, type NivelEspera } from "../utils/espera";

const STORAGE_KEY = "wati-alertas-avisadas";

function leerAvisadas(): Set<string> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

function guardarAvisadas(avisadas: Set<string>): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...avisadas]));
  } catch {
    // sessionStorage no disponible: el de-dup vive solo en memoria.
  }
}

function clave(p: ConversacionPendiente, nivel: NivelEspera): string {
  return `${p.wa_id}:${nivel}`;
}

function mostrarToast(p: ConversacionPendiente, nivel: NivelEspera, inboxUrl: string | null) {
  const titulo =
    nivel === "critico"
      ? `${p.nombre} lleva ${textoEspera(p.minutos_esperando).replace(/^hace /, "")} sin respuesta`
      : `${p.nombre} espera respuesta ${textoEspera(p.minutos_esperando)}`;
  const descripcion = p.sin_asignar
    ? "Chat sin asignar — nadie lo tiene."
    : `Asignado a ${p.operador_nombre ?? p.operador_email ?? "—"}.`;
  const opciones = {
    id: clave(p, nivel),
    description: descripcion,
    duration: Infinity,
    closeButton: true,
    action: inboxUrl
      ? { label: "Abrir WATI", onClick: () => window.open(inboxUrl, "_blank", "noopener") }
      : undefined,
  };
  if (nivel === "critico") toast.error(titulo, opciones);
  else toast.warning(titulo, opciones);
}

/** Avisa (toast persistente + sonido) cuando un chat cruza un umbral de
 * espera: una vez al llegar a "atención" y otra al llegar a "crítico", no
 * en cada refresco. El registro de avisados vive en sessionStorage para
 * sobrevivir a una recarga de la pestaña; cuando un chat deja de estar
 * pendiente (lo respondieron o lo cerraron) su aviso se retira solo y se
 * olvida, así que si vuelve a esperar se avisa de nuevo. Al pasar a
 * "crítico" el aviso rojo reemplaza al amarillo. El toast también se puede
 * descartar con la X o con "Abrir WATI". */
export function useWatiAlertas(pendientes: ConversacionPendiente[], inboxUrl: string | null) {
  const avisadas = useRef<Set<string> | null>(null);

  useEffect(() => {
    avisadas.current ??= leerAvisadas();
    const set = avisadas.current;
    const vigentes = new Set<string>();
    let nuevos = 0;
    for (const p of pendientes) {
      const nivel = nivelEspera(p.minutos_esperando);
      if (nivel === "ok") continue;
      const k = clave(p, nivel);
      vigentes.add(k);
      if (nivel === "critico") {
        vigentes.add(clave(p, "atencion"));
        toast.dismiss(clave(p, "atencion"));
      }
      if (set.has(k)) continue;
      set.add(k);
      mostrarToast(p, nivel, inboxUrl);
      nuevos += 1;
    }
    for (const k of [...set]) {
      if (vigentes.has(k)) continue;
      set.delete(k);
      toast.dismiss(k);
    }
    guardarAvisadas(set);
    if (nuevos > 0) sonarAviso();
  }, [pendientes, inboxUrl]);
}
