"use client";

import { useEffect, useState } from "react";
import { reporteIncidentesApi } from "../api/reporte-incidentes-api";
import type { Incidente } from "../types/reporte";
import type { EstadoDashboard } from "./use-reporte";

export const TAMANO_PAGINA_PENDIENTES = 50;

interface Resultado {
  clave: string;
  items: Incidente[];
  total: number;
  error: string | null;
}

/** Cola "Pendientes de revisión" del período completo (no sigue los filtros).
 * Solo consulta mientras el panel está abierto; recarga cuando sube `version`
 * (una corrección guardada saca al caso de la cola). */
export function usePendientes(estado: EstadoDashboard) {
  const { pedido, version } = estado;
  const [abierto, setAbierto] = useState(false);
  const [page, setPage] = useState(1);
  const [expandidas, setExpandidas] = useState<Set<string>>(new Set());

  const empresaId = pedido?.empresaId ?? "";
  const periodo = pedido?.periodo ?? "";
  const meses = pedido?.meses ?? 0;

  const clavePedido = `${empresaId}|${periodo}|${meses}`;
  const [pedidoPrevio, setPedidoPrevio] = useState(clavePedido);
  if (pedidoPrevio !== clavePedido) {
    setPedidoPrevio(clavePedido);
    setPage(1);
    setExpandidas(new Set());
  }

  const clave = `${clavePedido}|${page}|${version}`;
  const [resultado, setResultado] = useState<Resultado | null>(null);

  useEffect(() => {
    if (!abierto || !empresaId) return;
    let activo = true;
    reporteIncidentesApi
      .listPendientes({ empresaId, periodo, meses }, page, TAMANO_PAGINA_PENDIENTES)
      .then((p) => activo && setResultado({ clave, items: p.items, total: p.total, error: null }))
      .catch((err: unknown) => {
        if (!activo) return;
        console.error("Error al cargar los pendientes de revisión:", err);
        const mensaje = err instanceof Error ? err.message : "No se pudieron cargar los pendientes.";
        setResultado({ clave, items: [], total: 0, error: mensaje });
      });
    return () => {
      activo = false;
    };
  }, [abierto, clave, empresaId, periodo, meses, page]);

  const alternarFila = (id: string) =>
    setExpandidas((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  return {
    abierto,
    alternarAbierto: () => setAbierto((a) => !a),
    page,
    setPage,
    filas: resultado?.items ?? [],
    total: resultado?.total ?? 0,
    error: resultado?.error ?? null,
    cargando: abierto && resultado?.clave !== clave,
    expandidas,
    alternarFila,
  };
}
