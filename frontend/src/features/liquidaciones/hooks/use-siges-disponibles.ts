"use client";

import { useEffect, useState } from "react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { SigesEmpresa } from "../types/liquidaciones";

/** Empresas de Siges todavía sin vincular a un prestador (`null` = cargando). */
export function useSigesDisponibles() {
  const [disponibles, setDisponibles] = useState<SigesEmpresa[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    liquidacionesApi
      .getSigesPropuestas()
      .then((r) => setDisponibles(r.disponibles))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar Siges"));
  }, []);

  return { disponibles, error };
}
