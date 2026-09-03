"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";
import { BonoTecnicoDetalleModal } from "./bono-tecnico-detalle-modal";
import { buildBonoTecnicosColumns } from "./bono-tecnicos-columns";
import { SolicitudTvAdminModal } from "./solicitud-tv-admin-modal";
import { SolicitudesTvPendientes } from "./solicitudes-tv-pendientes";
import { monthValueToPeriodo, useBonoTecnicos } from "../hooks/use-bono-tecnicos";
import type { PuntajeTecnico } from "../types/bono-tecnicos";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { Spinner } from "@/shared/components/ui/spinner";
import { StatsTable } from "@/shared/components/ui/stats-table";

export function BonoTecnicosDetail() {
  const {
    canUpdate,
    canApprove,
    monthValue,
    setMonthValue,
    filas,
    loading,
    savingId,
    savingSugeridos,
    error,
    guardarInput,
    cargarSugeridos,
    crearSolicitudTvAdmin,
  } = useBonoTecnicos();
  const [detalleRow, setDetalleRow] = useState<PuntajeTecnico | null>(null);
  const [solicitudTvRow, setSolicitudTvRow] = useState<PuntajeTecnico | null>(null);

  const sinDiasCargados = filas.filter((f) => f.puntaje === null).length;

  const columns = buildBonoTecnicosColumns({
    canUpdate,
    savingId,
    onGuardarDias: (row: PuntajeTecnico, dias: number) => guardarInput(row.id_tecnico, dias),
    onVerDetalle: setDetalleRow,
    onCrearTv: setSolicitudTvRow,
  });

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">
            Bono Técnicos
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Puntaje mensual de los técnicos de calle para el cálculo del bono.
          </p>
        </div>
        <label className="flex flex-col gap-1">
          <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
            Período
          </span>
          <input
            type="month"
            value={monthValue}
            onChange={(e) => setMonthValue(e.target.value)}
            className="rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-orange/60"
          />
        </label>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && (
        <div className="flex flex-col gap-6">
          <SolicitudesTvPendientes
            periodo={monthValueToPeriodo(monthValue)}
            enabled={canApprove}
          />

          <KpiGrid>
            <KpiTile label="Técnicos con actividad" value={String(filas.length)} tone="neutral" />
            <KpiTile
              label="Sin Días cargados"
              value={String(sinDiasCargados)}
              tone={sinDiasCargados > 0 ? "danger" : "neutral"}
              hint="Puntaje pendiente de calcular"
            />
          </KpiGrid>

          {canUpdate && sinDiasCargados > 0 && (
            <div>
              <button
                type="button"
                disabled={savingSugeridos}
                onClick={() => void cargarSugeridos()}
                className="inline-flex items-center gap-2 rounded-[8px] border border-brand-orange bg-brand-orange/10 px-4 py-2 font-body text-sm font-bold text-brand-orange hover:bg-brand-orange/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {savingSugeridos && <Loader2 className="h-4 w-4 animate-spin" />}
                Cargar sugeridos ({sinDiasCargados})
              </button>
            </div>
          )}

          <StatsTable
            title="Puntaje por técnico"
            subtitle={canUpdate ? "Cargá Días para calcular el puntaje." : undefined}
            columns={columns}
            rows={filas}
            rowKey={(row) => String(row.id_tecnico)}
            emptyLabel="Sin técnicos con incidentes en el período seleccionado."
          />
        </div>
      )}

      {detalleRow && (
        <BonoTecnicoDetalleModal
          key={detalleRow.id_tecnico}
          tecnico={detalleRow.tecnico}
          periodo={monthValueToPeriodo(monthValue)}
          idTecnico={detalleRow.id_tecnico}
          onClose={() => setDetalleRow(null)}
        />
      )}

      {solicitudTvRow && (
        <SolicitudTvAdminModal
          key={solicitudTvRow.id_tecnico}
          tecnico={solicitudTvRow.tecnico}
          onClose={() => setSolicitudTvRow(null)}
          onSubmit={(body) => crearSolicitudTvAdmin(solicitudTvRow.id_tecnico, body)}
        />
      )}
    </div>
  );
}
