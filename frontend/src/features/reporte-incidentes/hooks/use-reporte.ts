"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { reporteIncidentesApi } from "../api/reporte-incidentes-api";
import type { DimensionFiltro, Filtros, PedidoReporte, Reporte } from "../types/reporte";
import { FILTROS_VACIOS, alternarFiltro, leerEstado, urlReporte } from "../lib/url-reporte";
import { useSession } from "@/services/session-provider";

/** Estado del dashboard: lee la URL, trae el reporte y expone cómo navegar
 * (filtros, rango). `version` sube cuando algo cambió del lado del servidor
 * (tipificación con IA o corrección manual) para que las partes recarguen. */
export function useReporte() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const { user, can } = useSession();
  const canUpdate = user.isSuperadmin || can("reporte-incidentes", "update");
  const estado = leerEstado(new URLSearchParams(params.toString()));
  const clave = params.toString();

  const [version, setVersion] = useState(0);
  // Cada respuesta recuerda a qué URL+versión corresponde: así se sabe, sin
  // setState dentro del efecto, si lo que está en pantalla quedó viejo.
  const [respuesta, setRespuesta] = useState<{
    de: string;
    reporte: Reporte | null;
    error: string | null;
  } | null>(null);
  const [navegando, startTransition] = useTransition();
  const pedidoActual = `${clave}#${version}`;

  useEffect(() => {
    const actual = leerEstado(new URLSearchParams(clave));
    if (!actual) return;
    let activo = true;
    const de = `${clave}#${version}`;
    reporteIncidentesApi
      .getReporte(actual.pedido, actual.filtros)
      .then((r) => activo && setRespuesta({ de, reporte: r, error: null }))
      .catch((err: unknown) => {
        if (!activo) return;
        console.error("Error al cargar el reporte de incidentes:", err);
        const mensaje = err instanceof Error ? err.message : "No se pudo cargar el reporte.";
        setRespuesta((previa) => ({ de, reporte: previa?.reporte ?? null, error: mensaje }));
      });
    return () => {
      activo = false;
    };
  }, [clave, version]);

  const reporte = respuesta?.reporte ?? null;
  const error = respuesta?.de === pedidoActual ? respuesta.error : null;
  const desactualizado = respuesta?.de !== pedidoActual;

  const navegar = useCallback(
    (pedido: PedidoReporte, filtros: Filtros) =>
      startTransition(() => router.push(urlReporte(pedido, filtros), { scroll: false })),
    [router],
  );

  // El pedido "efectivo" es el que devolvió el backend (período saneado, meses acotados).
  const pedido: PedidoReporte | null = reporte
    ? { empresaId: reporte.empresa.id, periodo: reporte.periodo, meses: reporte.meses }
    : (estado?.pedido ?? null);
  const filtros = reporte?.filtros ?? estado?.filtros ?? FILTROS_VACIOS;

  return {
    pathname,
    canUpdate,
    sinCliente: estado === null,
    pedido,
    filtros,
    reporte,
    error,
    cargando: reporte === null && error === null,
    /** Hay un reporte en pantalla pero corresponde a otra URL/versión (se está trayendo el nuevo). */
    actualizando: reporte !== null && desactualizado,
    navegando,
    version,
    recargar: () => setVersion((v) => v + 1),
    alternarFiltro: (dimension: DimensionFiltro, valor: string) =>
      pedido && navegar(pedido, alternarFiltro(filtros, dimension, valor)),
    quitarFiltro: (dimension: DimensionFiltro) =>
      pedido && navegar(pedido, { ...filtros, [dimension]: "" }),
    limpiarFiltros: () => pedido && navegar(pedido, FILTROS_VACIOS),
    cambiarRango: (periodo: string, meses: number) =>
      pedido && navegar({ ...pedido, periodo, meses }, filtros),
  };
}

export type EstadoDashboard = ReturnType<typeof useReporte>;
