"use client";

import { useCallback, useEffect, useState } from "react";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";

/** Ids de Siges ya dados de alta en el módulo SLA (otro módulo, catálogo
 * aparte). `null` = todavía no se pudo consultar (o el usuario no tiene
 * permiso sobre `prestadores`). Promise-chain en vez de async/await:
 * react-hooks/set-state-in-effect solo acepta setState en callbacks
 * .then/.catch (ver nota en siges-sync-modal.tsx). */
export function useAltasSla() {
  const [sigesConAltaSla, setSigesConAltaSla] = useState<Set<number> | null>(null);

  const refetch = useCallback(
    () =>
      prestadoresApi
        .getResumen()
        .then((resumen) => {
          const ids = resumen.grupos.flatMap((g) => g.prestadores.map((p) => p.sigesEmpresaId));
          setSigesConAltaSla(new Set(ids));
        })
        .catch((err: unknown) => {
          // Sin permiso sobre `prestadores`, u otro error — se oculta el botón
          // "Completar alta SLA" en vez de arriesgar una alta duplicada.
          console.error("No se pudo consultar el módulo SLA:", err);
        }),
    [],
  );

  useEffect(() => { void refetch(); }, [refetch]);

  return { sigesConAltaSla, refetch };
}
