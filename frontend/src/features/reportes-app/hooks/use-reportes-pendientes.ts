"use client";

import { useEffect, useState } from "react";
import { reportesAppApi } from "../api/reportes-app-api";

/** Novedades del circuito de reportes desde la última visita al panel: los
 * reportes cargados o que cambiaron de estado después de esa visita. Marca el
 * ícono del pie del menú lateral. La visita se guarda en el navegador (al
 * entrar y al salir del panel, así las decisiones tomadas adentro no cuentan). */

const POLL_INTERVAL_MS = 90_000;
const CLAVE_VISITA = "hdm.reportes-app.ultima-visita";
// ponytail: solo mira los 100 reportes más nuevos por fecha de carga; un cambio
// de estado en uno más viejo no prende el puntito. Pasar a un endpoint de
// "novedades desde" si alguna vez hay más de 100 reportes vivos.
const MAX_REVISADOS = 100;

function leerVisita(): number {
  try {
    return Number(localStorage.getItem(CLAVE_VISITA)) || 0;
  } catch {
    return 0; // Sin storage (incógnito bloqueado): todo cuenta como novedad.
  }
}

function guardarVisita() {
  try {
    localStorage.setItem(CLAVE_VISITA, String(Date.now()));
  } catch (err: unknown) {
    console.warn("[reportes-app] no se pudo guardar la visita al panel:", err);
  }
}

export function useReportesNovedades(enPanel: boolean): number {
  const [novedades, setNovedades] = useState(0);

  useEffect(() => {
    if (enPanel) {
      guardarVisita();
      return guardarVisita;
    }
    let cancelled = false;

    const load = async () => {
      try {
        const { items } = await reportesAppApi.listar(null, 1, MAX_REVISADOS);
        const desde = leerVisita();
        const cuenta = items.filter(
          (r) => Date.parse(r.actualizado_en ?? r.creado_en) > desde,
        ).length;
        if (!cancelled) setNovedades(cuenta);
      } catch (err: unknown) {
        // Indicador informativo: si falla queda sin marcar, sin romper el menú.
        if (!cancelled) {
          console.warn("[reportes-app] no se pudieron contar las novedades:", err);
          setNovedades(0);
        }
      }
    };
    const alVolver = () => {
      if (document.visibilityState === "visible") void load();
    };

    void load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    document.addEventListener("visibilitychange", alVolver);
    return () => {
      cancelled = true;
      clearInterval(interval);
      document.removeEventListener("visibilitychange", alVolver);
    };
  }, [enPanel]);

  // En el panel no hay nada que avisar; al salir, el próximo load recuenta.
  return enPanel ? 0 : novedades;
}
