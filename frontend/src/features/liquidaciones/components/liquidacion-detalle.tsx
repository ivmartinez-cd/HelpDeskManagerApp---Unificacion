"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Spinner } from "@/shared/components/ui/spinner";
import { ApiError } from "@/services/http-client";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { SeleccionAlertasProvider } from "../hooks/seleccion-alertas-context";
import type {
  Alerta,
  EstadoLiquidacion,
  EvolucionIncidentesItem,
  LiquidacionDetalle,
  PrestadorLiquidacion,
} from "../types/liquidaciones";
import { AbonoBanner } from "./abono-banner";
import { AlertasLoteBar } from "./alertas-lote-bar";
import { EvolucionIncidentesChart } from "./evolucion-incidentes-chart";
import { ExtraItemSeccion } from "./extra-item-seccion";
import { IncidentesSeccion } from "./incidentes-seccion";
import { LiquidacionAlertasBanner } from "./liquidacion-alertas-banner";
import { LiquidacionConfigBanner } from "./liquidacion-config-banner";
import { LiquidacionDetalleHeader } from "./liquidacion-detalle-header";
import { ModeloFacturacionSeccion } from "./modelo-facturacion-seccion";

export function LiquidacionDetalleView({ id }: { id: string }) {
  const router = useRouter();
  const [detalle, setDetalle] = useState<LiquidacionDetalle | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [reanalizing, setReanalizing] = useState(false);
  const [updatingEstado, setUpdatingEstado] = useState(false);
  const [soloConAlertas, setSoloConAlertas] = useState(false);
  const [evolucion, setEvolucion] = useState<EvolucionIncidentesItem[] | null>(null);

  const load = useCallback(
    () =>
      Promise.all([liquidacionesApi.get(id), liquidacionesApi.listPrestadores(false)])
        .then(([det, prest]) => {
          setDetalle(det);
          setPrestadores(prest);
        })
        .catch((err: unknown) => {
          if (err instanceof ApiError && err.status === 404) setNotFound(true);
          else throw err;
        })
        .finally(() => setLoading(false)),
    [id],
  );

  useEffect(() => { void load(); }, [load]);

  // Histórico del prestador (todas sus liquidaciones, no solo esta) para el
  // gráfico de evolución — no bloquea el render del detalle si falla, y no se
  // re-pide en cada refresh silencioso (solo cambia si cambia de prestador).
  const prestadorId = detalle?.liquidacion.prestadorId;
  useEffect(() => {
    if (!prestadorId) return;
    let cancelado = false;
    liquidacionesApi
      .getEvolucionIncidentes(prestadorId)
      .then((items) => { if (!cancelado) setEvolucion(items); })
      .catch((err: unknown) => {
        console.error("No se pudo cargar la evolución de incidentes del prestador", err);
        if (!cancelado) setEvolucion([]);
      });
    return () => { cancelado = true; };
  }, [prestadorId]);

  // Refresh silencioso al abrir el detalle: reconcilia esta liquidación contra
  // AyC (estado, costos/km de incidentes) una sola vez por visita a la página.
  // Best-effort — un fallo acá nunca debe impedir ver el detalle ya cargado.
  const reconciliadoRef = useRef(false);
  useEffect(() => {
    if (!detalle || reconciliadoRef.current) return;
    reconciliadoRef.current = true;
    const { numeroLiquidacion, estado } = detalle.liquidacion;
    if (!numeroLiquidacion || estado === "aprobada" || estado === "cerrada") return;
    void liquidacionesApi
      .reconciliar(id)
      .catch(() => {})
      .then(() => load());
  }, [detalle, id, load]);

  const handleReanalizar = async () => {
    setReanalizing(true);
    try {
      await liquidacionesApi.reanalyze(id);
      await load();
    } catch (err: unknown) {
      toast.error(err instanceof ApiError ? err.message : "No se pudo reanalizar la liquidación.");
    } finally {
      setReanalizing(false);
    }
  };

  const handleUpdateEstado = async (nuevoEstado: EstadoLiquidacion) => {
    if (!detalle) return;
    setUpdatingEstado(true);
    try {
      const updated = await liquidacionesApi.updateEstado(id, nuevoEstado);
      setDetalle({ ...detalle, liquidacion: updated });
    } catch (err: unknown) {
      toast.error(err instanceof ApiError ? err.message : "No se pudo actualizar el estado.");
    } finally {
      setUpdatingEstado(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Spinner />
      </div>
    );
  }

  if (notFound || !detalle) {
    return (
      <div className="flex flex-col items-center gap-4 p-16">
        <p className="font-heading text-xl font-extrabold text-foreground">
          Liquidación no encontrada
        </p>
        <p className="font-body text-sm text-muted-foreground">
          Puede que se haya eliminado o que el enlace sea viejo.
        </p>
        <Link
          href="/liquidaciones/lista"
          className="font-body text-sm font-semibold text-brand-orange hover:underline"
        >
          ← Volver a la lista de liquidaciones
        </Link>
      </div>
    );
  }

  const { liquidacion, incidentes, alertas } = detalle;
  const pstMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const pst = pstMap[liquidacion.prestadorId];
  const alertasByInc = alertas.reduce<Record<string, Alerta[]>>((acc, a) => {
    (acc[a.incidenteId] ??= []).push(a);
    return acc;
  }, {});
  const incConAlertas = Object.keys(alertasByInc).length;
  // `liquidacion.totalAlertas` es el contador que fija el motor de reglas al
  // importar/reanalizar (cuántas alertas generó esa corrida) — no baja cuando
  // la TL resuelve/descarta una alerta individual (ver ActualizarEstadoAlerta,
  // que no lo toca). El KPI del header cuenta INCIDENTES con alguna alerta
  // pendiente/en_revisión, no alertas sueltas: un mismo incidente puede tener
  // 2-3 alertas (ALT005 grupo + individual, por ejemplo) y sumarlas todas
  // infla el número sin que represente más trabajo real para la TL (pedido de
  // Iván, 2026-09-09). Se calcula sobre `alertasByInc` (siempre fresco tras
  // cada `load()`).
  const incidentesConAlertaActiva = Object.values(alertasByInc).filter((as) =>
    as.some((a) => a.estado === "pendiente" || a.estado === "en_revision"),
  ).length;
  const correctivos = incidentes.filter((i) => i.tipo.toLowerCase() !== "preventivo");
  const preventivos = incidentes.filter((i) => i.tipo.toLowerCase() === "preventivo");
  // Todos los incidentes de la liquidación (no solo los de la sección que se
  // está renderizando) — permite vincular/mostrar una ruta compartida con un
  // incidente de la otra sección (correctivos ⇄ preventivos).
  const incidentesById = Object.fromEntries(incidentes.map((i) => [i.id, i]));

  return (
    <SeleccionAlertasProvider alertasByInc={alertasByInc}>
    <div className="flex flex-col gap-5 p-6">
      <Link
        href="/liquidaciones/lista"
        className="flex w-fit items-center gap-1.5 font-body text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        ← Lista de liquidaciones
      </Link>

      {/* Header */}
      <LiquidacionDetalleHeader
        liquidacion={liquidacion}
        incidentesConAlertaActiva={incidentesConAlertaActiva}
        pst={pst}
        reanalizing={reanalizing}
        onReanalizar={() => void handleReanalizar()}
        updatingEstado={updatingEstado}
        onUpdateEstado={(nuevo) => void handleUpdateEstado(nuevo)}
        onActualizado={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
        onAnulado={() => router.push("/liquidaciones/lista")}
      />

      {evolucion && evolucion.length > 0 && (
        <div className="flex flex-col gap-2 rounded-[12px] border border-border bg-card p-4">
          <span className="font-heading text-[13px] font-bold text-foreground">
            Evolución mensual de incidentes por tipo — {pst?.nombreCorto ?? "prestador"} (
            {new Date().getFullYear()})
          </span>
          <EvolucionIncidentesChart items={evolucion} />
        </div>
      )}

      {/* Banner de alertas */}
      {incConAlertas > 0 && (
        <LiquidacionAlertasBanner
          incConAlertas={incConAlertas}
          soloConAlertas={soloConAlertas}
          onSoloConAlertas={setSoloConAlertas}
        />
      )}

      <AbonoBanner liquidacion={liquidacion} totalIncidentes={incidentes.length} />

      <LiquidacionConfigBanner alertas={alertas} incidentes={incidentes} />

      <ExtraItemSeccion
        liquidacion={liquidacion}
        onUpdated={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
      />

      <IncidentesSeccion
        liquidacionId={id}
        prestadorId={liquidacion.prestadorId}
        prestadores={prestadores}
        titulo="Correctivos"
        accentClass="text-brand-orange"
        incidentes={correctivos}
        incidentesById={incidentesById}
        alertasByInc={alertasByInc}
        soloConAlertas={soloConAlertas}
        onAlertaChanged={() => void load()}
      />
      {preventivos.length > 0 && (
        <IncidentesSeccion
          liquidacionId={id}
          prestadorId={liquidacion.prestadorId}
          prestadores={prestadores}
          titulo="Preventivos"
          accentClass="text-emerald-500"
          incidentes={preventivos}
          incidentesById={incidentesById}
          alertasByInc={alertasByInc}
          soloConAlertas={soloConAlertas}
          onAlertaChanged={() => void load()}
        />
      )}

      <ModeloFacturacionSeccion incidentes={incidentes} totalImporte={liquidacion.totalImporte} />

      {/* Gestión de alertas en lote: aparece al tildar incidentes */}
      <AlertasLoteBar liquidacionId={id} onChanged={() => void load()} />
    </div>
    </SeleccionAlertasProvider>
  );
}
