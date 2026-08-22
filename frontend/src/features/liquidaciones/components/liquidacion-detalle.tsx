"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Spinner } from "@/shared/components/ui/spinner";
import { ApiError } from "@/services/http-client";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  Alerta,
  EstadoLiquidacion,
  LiquidacionDetalle,
  PrestadorLiquidacion,
} from "../types/liquidaciones";
import { AlertasSeccion } from "./alertas-seccion";
import { ExtraItemSeccion } from "./extra-item-seccion";
import { IncidentesSeccion } from "./incidentes-seccion";
import { LiquidacionAlertasBanner } from "./liquidacion-alertas-banner";
import { LiquidacionDetalleHeader } from "./liquidacion-detalle-header";
import { ModeloFacturacionSeccion } from "./modelo-facturacion-seccion";
import { ObservacionesSeccion } from "./observaciones-seccion";

export function LiquidacionDetalleView({ id }: { id: string }) {
  const router = useRouter();
  const [detalle, setDetalle] = useState<LiquidacionDetalle | null>(null);
  const [prestadores, setPrestadores] = useState<PrestadorLiquidacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [reanalizing, setReanalizing] = useState(false);
  const [updatingEstado, setUpdatingEstado] = useState(false);
  const [soloConAlertas, setSoloConAlertas] = useState(false);

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

  const { liquidacion, incidentes, alertas, observaciones } = detalle;
  const pstMap = Object.fromEntries(prestadores.map((p) => [p.id, p]));
  const pst = pstMap[liquidacion.prestadorId];
  const alertasByInc = alertas.reduce<Record<string, Alerta[]>>((acc, a) => {
    (acc[a.incidenteId] ??= []).push(a);
    return acc;
  }, {});
  const incConAlertas = Object.keys(alertasByInc).length;
  const correctivos = incidentes.filter((i) => i.tipo.toLowerCase() !== "preventivo");
  const preventivos = incidentes.filter((i) => i.tipo.toLowerCase() === "preventivo");

  return (
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
        pst={pst}
        reanalizing={reanalizing}
        onReanalizar={() => void handleReanalizar()}
        updatingEstado={updatingEstado}
        onUpdateEstado={(nuevo) => void handleUpdateEstado(nuevo)}
        onActualizado={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
        onAnulado={() => router.push("/liquidaciones/lista")}
      />

      {/* Banner de alertas */}
      {incConAlertas > 0 && (
        <LiquidacionAlertasBanner
          incConAlertas={incConAlertas}
          soloConAlertas={soloConAlertas}
          onSoloConAlertas={setSoloConAlertas}
        />
      )}

      <ExtraItemSeccion
        liquidacion={liquidacion}
        onUpdated={(updated) => setDetalle({ ...detalle, liquidacion: updated })}
      />

      <IncidentesSeccion
        titulo="Correctivos"
        accentClass="text-brand-orange"
        incidentes={correctivos}
        alertasByInc={alertasByInc}
        soloConAlertas={soloConAlertas}
      />
      {preventivos.length > 0 && (
        <IncidentesSeccion
          titulo="Preventivos"
          accentClass="text-emerald-500"
          incidentes={preventivos}
          alertasByInc={alertasByInc}
          soloConAlertas={soloConAlertas}
        />
      )}

      <ModeloFacturacionSeccion incidentes={incidentes} totalImporte={liquidacion.totalImporte} />

      <AlertasSeccion
        liquidacionId={id}
        prestadorId={liquidacion.prestadorId}
        prestadores={prestadores}
        alertas={alertas}
        incidentes={incidentes}
        onChanged={() => void load()}
      />

      <ObservacionesSeccion
        liquidacionId={id}
        observaciones={observaciones}
        onChanged={() => void load()}
      />
    </div>
  );
}
