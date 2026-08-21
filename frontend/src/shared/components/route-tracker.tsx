"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import { accesosApi } from "@/features/home/api/accesos-api";
import { findAcceso } from "@/features/home/config/accesos-catalogo";

/** No renderiza nada: solo observa la navegación y postea la visita al
 * backend para el ranking de accesos directos de Inicio. Montado una sola
 * vez en `app/(app)/layout.tsx`, fuera del grupo `(auth)`.
 *
 * `lastPosted` evita tanto el doble disparo de StrictMode en dev (el efecto
 * corre dos veces para el mismo pathname en el mount inicial) como reposteos
 * si el efecto se re-ejecuta sin que la ruta haya cambiado en los hechos.
 * Falla en silencio: la telemetría nunca puede romper la navegación. */
export function RouteTracker() {
  const pathname = usePathname();
  const lastPosted = useRef<string | null>(null);

  useEffect(() => {
    if (!pathname || pathname === lastPosted.current) return;
    lastPosted.current = pathname;
    if (!findAcceso(pathname)) return;
    accesosApi.recordVisit(pathname).catch(() => {
      // best-effort -- ver docstring.
    });
  }, [pathname]);

  return null;
}
