"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";
import { sonarAviso } from "@/shared/utils/beep";
import type { ModificacionPrestador } from "../types/modificacion";
import { mostrarToastModificacion, retirarToastModificacion } from "../utils/toast-modificaciones";

interface GrupoModificaciones {
  liquidacionId: string;
  numeroLiquidacion: string | null;
  cantidad: number;
}

function agrupar(noVistas: ModificacionPrestador[]): GrupoModificaciones[] {
  const porLiquidacion = new Map<string, GrupoModificaciones>();
  for (const m of noVistas) {
    const grupo = porLiquidacion.get(m.liquidacionId);
    if (grupo) {
      grupo.cantidad += 1;
    } else {
      porLiquidacion.set(m.liquidacionId, {
        liquidacionId: m.liquidacionId,
        numeroLiquidacion: m.numeroLiquidacion,
        cantidad: 1,
      });
    }
  }
  return [...porLiquidacion.values()];
}

/** Un toast persistente por liquidación con modificaciones del prestador sin
 * ver, con sonido la primera vez que aparece — mismo mecanismo que
 * `useWatiAvisos`. El toast se retira solo cuando la liquidación deja de
 * tener modificaciones sin ver (se marcaron vistas en el detalle, o el
 * próximo polling ya no las trae). */
export function useModificacionesAvisos(noVistas: ModificacionPrestador[], activo: boolean): void {
  const router = useRouter();
  const toastsAbiertos = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!activo) {
      for (const id of toastsAbiertos.current) retirarToastModificacion(id);
      toastsAbiertos.current.clear();
      return;
    }
    const grupos = agrupar(noVistas);
    const vigentes = new Set(grupos.map((g) => g.liquidacionId));
    let huboNuevo = false;

    for (const id of [...toastsAbiertos.current]) {
      if (vigentes.has(id)) continue;
      retirarToastModificacion(`modificaciones:${id}`);
      toastsAbiertos.current.delete(id);
    }

    for (const grupo of grupos) {
      if (!toastsAbiertos.current.has(grupo.liquidacionId)) huboNuevo = true;
      mostrarToastModificacion(
        `modificaciones:${grupo.liquidacionId}`,
        grupo.numeroLiquidacion,
        grupo.cantidad,
        () => router.push(`/liquidaciones/${grupo.liquidacionId}`),
      );
      toastsAbiertos.current.add(grupo.liquidacionId);
    }

    if (huboNuevo) sonarAviso();
  }, [noVistas, activo, router]);
}
