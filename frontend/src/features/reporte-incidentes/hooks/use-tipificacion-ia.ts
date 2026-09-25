"use client";

import { useEffect, useEffectEvent, useRef, useState } from "react";
import { reporteIncidentesApi } from "../api/reporte-incidentes-api";
import type { PedidoReporte, Reporte, ResultadoIA } from "../types/reporte";
import type { EstadoDashboard } from "./use-reporte";
import { ApiError } from "@/services/http-client";

export type FaseIA = "inactiva" | "tipificando" | "exito" | "saturada" | "no_configurada" | "error";

interface EstadoIA {
  fase: FaseIA;
  inicio: number;
  duracionMs: number;
  resultado: ResultadoIA | null;
  mensaje: string | null;
}

const INACTIVA: EstadoIA = { fase: "inactiva", inicio: 0, duracionMs: 0, resultado: null, mensaje: null };
const MS_EXITO_VISIBLE = 4000;

/** Cronómetro que avanza solo mientras `activo`. */
function useAhora(activo: boolean): number {
  const [ahora, setAhora] = useState(() => Date.now());
  useEffect(() => {
    if (!activo) return;
    const handle = setInterval(() => setAhora(Date.now()), 100);
    return () => clearInterval(handle);
  }, [activo]);
  return ahora;
}

/** Port de `ClassificationRefiner`: si el reporte trae casos sin tipificar y
 * el usuario tiene permiso, dispara la tipificación con IA una sola vez por
 * pedido + `version` (los refs sobreviven al doble montaje de StrictMode; un
 * cambio de filtros no vuelve a disparar). Si tipificó algo, recarga el
 * dashboard y el reporte nuevo vuelve a disparar solo si todavía quedan
 * pendientes (avanza por tandas, como el legacy). Si la IA no tipificó nada,
 * se queda quieta y ofrece reintentar; si falta la API key, no reintenta más. */
export function useTipificacionIA(estado: EstadoDashboard) {
  const { reporte, pedido, canUpdate, recargar } = estado;
  const [ia, setIa] = useState<EstadoIA>(INACTIVA);
  // Lo último que disparó: el pedido+version y el reporte vigente en ese momento.
  // Tras `recargar()` sube la version pero el reporte viejo sigue hasta que
  // llega el nuevo: exigir ambos cambios evita disparar con datos viejos.
  const ultimo = useRef<{ clave: string; reporte: Reporte | null }>({ clave: "", reporte: null });
  const corriendo = useRef(false);
  const sinConfigurar = useRef(false);
  const ahora = useAhora(ia.fase === "tipificando");

  const ejecutar = async (objetivo: PedidoReporte) => {
    if (corriendo.current) return;
    corriendo.current = true;
    const inicio = Date.now();
    setIa({ ...INACTIVA, fase: "tipificando", inicio });
    try {
      const resultado = await reporteIncidentesApi.tipificar(objetivo);
      const duracionMs = Date.now() - inicio;
      const fase: FaseIA =
        resultado.tipificados > 0 ? "exito" : resultado.fallidos > 0 ? "saturada" : "inactiva";
      setIa({ fase, inicio, duracionMs, resultado, mensaje: null });
      if (resultado.tipificados > 0) recargar();
    } catch (err: unknown) {
      const duracionMs = Date.now() - inicio;
      if (err instanceof ApiError && err.code === "IA_NO_CONFIGURADA") {
        sinConfigurar.current = true;
        setIa({ fase: "no_configurada", inicio, duracionMs, resultado: null, mensaje: err.message });
      } else {
        console.error("Error al tipificar con IA:", err);
        const mensaje = err instanceof Error ? err.message : "No se pudo tipificar con IA.";
        setIa({ fase: "error", inicio, duracionMs, resultado: null, mensaje });
      }
    } finally {
      corriendo.current = false;
    }
  };

  const pendientes = reporte?.pendientes_ia ?? 0;
  const alRecibirReporte = useEffectEvent(() => {
    if (!reporte || !pedido || !canUpdate || reporte.pendientes_ia <= 0) return;
    if (corriendo.current || sinConfigurar.current) return;
    const clave = `${pedido.empresaId}|${pedido.periodo}|${pedido.meses}|${estado.version}`;
    if (ultimo.current.clave === clave || ultimo.current.reporte === reporte) return;
    ultimo.current = { clave, reporte };
    const objetivo = { ...pedido };
    // Por microtask: `ejecutar` escribe estado y el linter lo contaría como
    // setState sincrónico dentro del efecto.
    queueMicrotask(() => void ejecutar(objetivo));
  });
  useEffect(() => alRecibirReporte(), [reporte, canUpdate]);

  // El aviso de éxito se va solo.
  useEffect(() => {
    if (ia.fase !== "exito") return;
    const handle = setTimeout(() => setIa(INACTIVA), MS_EXITO_VISIBLE);
    return () => clearTimeout(handle);
  }, [ia.fase]);

  return {
    ...ia,
    pendientes,
    transcurridoMs: ia.fase === "tipificando" ? Math.max(0, ahora - ia.inicio) : ia.duracionMs,
    reintentar: () => pedido && void ejecutar({ ...pedido }),
    cerrar: () => setIa(INACTIVA),
  };
}
