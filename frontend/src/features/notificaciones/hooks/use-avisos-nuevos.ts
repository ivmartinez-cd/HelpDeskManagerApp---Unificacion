"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import type { DesktopNotificationPayload } from "@/shared/hooks/use-desktop-notifications";
import { sonarAviso } from "@/shared/utils/beep";
import type { Notificacion } from "../api/notificaciones-api";

/** Toasts como máximo por tanda: el primer ciclo de un job nuevo puede traer
 * decenas de golpe, y el resto igual queda en la campanita. */
const MAX_TOASTS = 3;
const TOAST_MS = 12_000;

/** Aviso activo (toast + sonido + notificación de escritorio si está
 * prendida) de las no leídas que aparecen mientras la pestaña está abierta.
 * Las que ya estaban al cargar la app no se anuncian: esas las muestra el
 * badge. Cada pestaña abierta avisa por su cuenta. */
export function useAvisosNuevos(
  noLeidas: Notificacion[],
  cargado: boolean,
  abrir: (n: Notificacion) => void,
  notificarEscritorio: (payload: DesktopNotificationPayload) => void,
): void {
  const vistas = useRef<Set<string> | null>(null);

  useEffect(() => {
    if (!cargado) return;
    if (vistas.current === null) {
      vistas.current = new Set(noLeidas.map((n) => n.id));
      return;
    }
    const conocidas = vistas.current;
    const nuevas = noLeidas.filter((n) => !conocidas.has(n.id));
    nuevas.forEach((n) => conocidas.add(n.id));
    if (nuevas.length === 0) return;

    sonarAviso();
    for (const n of nuevas.slice(0, MAX_TOASTS)) {
      toast.info(n.titulo, {
        id: `notificacion:${n.id}`,
        description: n.cuerpo,
        duration: TOAST_MS,
        closeButton: true,
        action: n.url ? { label: "Ver", onClick: () => abrir(n) } : undefined,
      });
    }
    if (nuevas.length > MAX_TOASTS) {
      toast.info(`Y ${nuevas.length - MAX_TOASTS} notificación(es) más en la campanita`);
    }
    notificarEscritorio(resumenEscritorio(nuevas));
  }, [noLeidas, cargado, abrir, notificarEscritorio]);
}

function resumenEscritorio(nuevas: Notificacion[]): DesktopNotificationPayload {
  const [primera] = nuevas;
  if (nuevas.length === 1) {
    return {
      title: primera.titulo,
      body: primera.cuerpo,
      tag: `notificacion:${primera.id}`,
      url: primera.url ?? "/",
    };
  }
  return {
    title: `${nuevas.length} notificaciones nuevas`,
    body: nuevas.map((n) => n.titulo).slice(0, 4).join("\n"),
    tag: "notificaciones:tanda",
    url: primera.url ?? "/",
  };
}
