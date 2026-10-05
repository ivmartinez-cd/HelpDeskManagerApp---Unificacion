"use client";

import { useEffect, useState } from "react";
import { bitacoraApi } from "../api/bitacora-api";
import type { EntradaBitacora } from "../types/bitacora";

/** Hilo de Web Agentes de la liquidación. `items` en `null` = cargando. Se
 * carga al abrir el detalle (no al entrar a la pestaña) para mostrar el
 * contador en la pestaña. */
export function useBitacoraLiquidacion(liquidacionId: string) {
  const [items, setItems] = useState<EntradaBitacora[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    bitacoraApi
      .listByLiquidacion(liquidacionId)
      .then((pagina) => setItems(pagina.items))
      .catch((err: unknown) => {
        console.error("Error al cargar la bitácora de la liquidación:", err);
        setError(true);
      });
  }, [liquidacionId]);

  return { items, error };
}
