"use client";

import { useCallback, useEffect, useState } from "react";
import { notificacionesApi, type Notificacion } from "../api/notificaciones-api";

const SIZE = 20;
/** Tope del backend por página: el historial muestra hasta las 100 últimas. */
const MAX = 100;

export interface HistorialState {
  items: Notificacion[];
  hayMas: boolean;
  cargando: boolean;
  error: string | null;
  cargarMas: () => void;
}

/** Leídas y no leídas, de la más reciente a la más vieja (el panel solo se
 * monta abierto). "Ver más" agranda la página en vez de sumar páginas, así
 * cuando `recarga` cambia (el polling trajo novedades o se marcó algo) se
 * relee todo lo que está a la vista de una sola vez, sin huecos ni repetidas. */
export function useHistorial(recarga: unknown): HistorialState {
  const [paginas, setPaginas] = useState(1);
  const [items, setItems] = useState<Notificacion[]>([]);
  const [total, setTotal] = useState(0);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- indicador de carga de un fetch disparado por el efecto
    setCargando(true);
    notificacionesApi
      .listar({ soloNoLeidas: false, page: 1, size: Math.min(SIZE * paginas, MAX) })
      .then((page) => {
        if (!alive) return;
        setItems(page.items);
        setTotal(page.total);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error("Error al cargar el historial de notificaciones:", err);
        if (alive) setError("No se pudieron cargar las notificaciones.");
      })
      .finally(() => {
        if (alive) setCargando(false);
      });
    return () => {
      alive = false;
    };
  }, [paginas, recarga]);

  const cargarMas = useCallback(() => setPaginas((p) => p + 1), []);
  return { items, hayMas: items.length < total && SIZE * paginas < MAX, cargando, error, cargarMas };
}
