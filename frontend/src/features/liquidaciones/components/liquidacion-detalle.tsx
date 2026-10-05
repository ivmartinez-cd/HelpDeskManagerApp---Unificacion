"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Spinner } from "@/shared/components/ui/spinner";
import { ApiError } from "@/services/http-client";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { useBitacoraLiquidacion } from "../hooks/use-bitacora-liquidacion";
import { useModificacionesLiquidacion } from "../hooks/use-modificaciones-liquidacion";
import { useEvolucionIncidentes, useLiquidacionDetalle } from "../hooks/use-liquidacion-detalle";
import { MonedaProvider } from "../hooks/moneda-context";
import { SeleccionAlertasProvider } from "../hooks/seleccion-alertas-context";
import type { Alerta, EstadoLiquidacion } from "../types/liquidaciones";
import { AbonoBanner } from "./abono-banner";
import { AlertasLoteBar } from "./alertas-lote-bar";
import { BitacoraSeccion } from "./bitacora-seccion";
import { DetalleTabs, type DetalleTab } from "./detalle-tabs";
import { EvolucionIncidentesChart } from "./evolucion-incidentes-chart";
import { ExtraItemSeccion } from "./extra-item-seccion";
import { IncidentesSeccion } from "./incidentes-seccion";
import { LiquidacionAlertasBanner } from "./liquidacion-alertas-banner";
import { LiquidacionConfigBanner } from "./liquidacion-config-banner";
import { LiquidacionDetalleHeader } from "./liquidacion-detalle-header";
import { ModeloFacturacionSeccion } from "./modelo-facturacion-seccion";
import { ModificacionesPrestadorSeccion } from "./modificaciones-prestador-seccion";

export function LiquidacionDetalleView({ id }: { id: string }) {
  const router = useRouter();
  const { detalle, setDetalle, prestadores, loading, notFound, refetch: load } = useLiquidacionDetalle(id);
  const [reanalizing, setReanalizing] = useState(false);
  const [updatingEstado, setUpdatingEstado] = useState(false);
  const [soloConAlertas, setSoloConAlertas] = useState(false);
  const [tab, setTab] = useState<DetalleTab>("detalle");
  const bitacora = useBitacoraLiquidacion(id);
  const modificaciones = useModificacionesLiquidacion(id);
  const evolucion = useEvolucionIncidentes(detalle?.liquidacion.prestadorId);

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
    <MonedaProvider cotizacion={detalle.cotizacionUsd}>
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

      <DetalleTabs
        value={tab}
        onChange={setTab}
        counts={{
          detalle: incidentesConAlertaActiva,
          modificaciones: modificaciones.items.length,
          bitacora: bitacora.items ? bitacora.items.length : null,
        }}
        destacadas={{ modificaciones: modificaciones.items.some((m) => m.vistaEn === null) }}
      />

      {tab === "detalle" && (
        <>
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
        </>
      )}

      {/* Historial de cambios que el prestador aplicó sobre esta liquidación
          (ADR-038) — no son alertas del motor. */}
      {tab === "modificaciones" && (
        <ModificacionesPrestadorSeccion liquidacionId={id} {...modificaciones} />
      )}

      {tab === "facturacion" && (
        <>
          <ExtraItemSeccion
            liquidacion={liquidacion}
            onUpdated={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
          />

          <ModeloFacturacionSeccion incidentes={incidentes} totalImporte={liquidacion.totalImporte} />

          {evolucion && evolucion.length > 0 && (
            <div className="flex flex-col gap-2 rounded-[12px] border border-border bg-card p-4">
              <span className="font-heading text-[13px] font-bold text-foreground">
                Evolución mensual de incidentes por tipo — {pst?.nombreCorto ?? "prestador"} (
                {new Date().getFullYear()})
              </span>
              <EvolucionIncidentesChart items={evolucion} />
            </div>
          )}
        </>
      )}

      {tab === "bitacora" && <BitacoraSeccion items={bitacora.items} error={bitacora.error} />}

      {/* Gestión de alertas en lote: aparece al tildar incidentes */}
      <AlertasLoteBar liquidacionId={id} onChanged={() => void load()} />
    </div>
    </SeleccionAlertasProvider>
    </MonedaProvider>
  );
}
