"use client";

import { RefreshCw } from "lucide-react";
import {
  INCIDENTES_PAGE_SIZE,
  MIS_PST,
  TODOS,
  formatUpdatedAt,
  useSlaDetail,
} from "../hooks/use-sla-detail";
import { incidenteColumns } from "./sla-incidentes-columns";
import { BrandButton, BrandSelect } from "@/shared/components/ui/brand-form";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { PaginationBar } from "@/shared/components/ui/pagination-bar";
import { SigesLoadingModal } from "@/shared/components/ui/siges-loading-modal";
import { StatsTable } from "@/shared/components/ui/stats-table";
import { Spinner } from "@/shared/components/ui/spinner";

export function SlaDetail() {
  const {
    canUpdate,
    canVerOperadores,
    monthValue,
    setMonthValue,
    scope,
    setScope,
    operadores,
    resumen,
    incidentes,
    totalIncidentes,
    page,
    setPage,
    loading,
    refreshing,
    error,
    handleRefresh,
  } = useSlaDetail();

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">SLA</h1>
          <p className="font-body text-sm text-muted-foreground">
            Cumplimiento de acuerdos de nivel de servicio por período.
          </p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
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
          <BrandSelect
            label="Vencidos de"
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            className="min-w-[180px]"
          >
            <option value={MIS_PST}>Mis PST</option>
            <option value={TODOS}>Todos</option>
            {canVerOperadores &&
              operadores.map((op) => (
                <option key={op.id} value={op.id}>
                  {op.fullName}
                </option>
              ))}
          </BrandSelect>
          <div className="flex flex-col items-end gap-1">
            <BrandButton
              onClick={handleRefresh}
              loading={refreshing}
              disabled={!canUpdate || loading}
              title={canUpdate ? undefined : "Sin permiso para actualizar"}
            >
              {!refreshing && <RefreshCw className="h-4 w-4" />}
              Actualizar
            </BrandButton>
            {resumen && (
              <span className="font-body text-[11px] text-muted-foreground">
                Actualizado {formatUpdatedAt(resumen.updated_at)}
              </span>
            )}
          </div>
        </div>
      </div>

      {loading && (
        <>
          {/* Un período ya snapshoteado responde en <1s y el modal ni aparece
              (delay de 1s); uno nuevo/viejo dispara la consulta completa a
              MERCURIO (~40s) y acá el modal evita el spinner eterno. */}
          <SigesLoadingModal
            etapas={[
              { hasta: 3, texto: "Buscando el resumen del período…" },
              {
                hasta: 15,
                texto: "El período no tenía datos precalculados — consultando en vivo…",
              },
              { hasta: 35, texto: "Cruzando incidentes y tiempos del período…" },
              { texto: "Un momento más — la consulta completa ronda los 40 segundos…" },
            ]}
            nota="Los períodos ya consultados se sirven al instante desde el snapshot local; uno nuevo requiere la consulta completa a MERCURIO (~40 segundos, queda guardada)."
          />
          <div className="flex h-64 items-center justify-center">
            <Spinner />
          </div>
        </>
      )}

      {refreshing && (
        <SigesLoadingModal
          etapas={[
            { hasta: 10, texto: "Recalculando el período en vivo…" },
            { hasta: 25, texto: "Cruzando incidentes y tiempos del período…" },
            { hasta: 40, texto: "Un momento más, ya casi está…" },
            { texto: "La base está lenta hoy — seguimos esperando la respuesta…" },
          ]}
          nota="Actualizar fuerza la consulta completa a MERCURIO (~40 segundos) y recalcula el snapshot del período."
        />
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && resumen && (
        <div className="flex flex-col gap-6">
          <KpiGrid>
            <KpiTile
              label="Total de incidentes"
              value={resumen.total.toLocaleString("es-AR")}
              tone="neutral"
            />
            <KpiTile
              label="Correctos"
              value={resumen.correctos.toLocaleString("es-AR")}
              tone="orange"
              hint={`${resumen.pct_correctos.toLocaleString("es-AR", { maximumFractionDigits: 2 })}% del período`}
            />
            <KpiTile
              label="Vencidos"
              value={resumen.vencidos.toLocaleString("es-AR")}
              tone={resumen.vencidos > 0 ? "danger" : "neutral"}
              hint={`${resumen.pct_vencidos.toLocaleString("es-AR", { maximumFractionDigits: 2 })}% del período`}
            />
          </KpiGrid>

          <StatsTable
            title="Incidentes vencidos"
            subtitle={
              resumen.vencidos_por_tecnico.length > 0
                ? resumen.vencidos_por_tecnico
                    .map((t) => `${t.tecnico}: ${t.cantidad}`)
                    .join(" · ")
                : undefined
            }
            columns={incidenteColumns}
            rows={incidentes}
            rowKey={(row) => String(row.id_incidente)}
            emptyLabel="Sin incidentes vencidos en el período seleccionado."
          />
          {totalIncidentes > 0 && (
            <PaginationBar
              page={page}
              total={totalIncidentes}
              size={INCIDENTES_PAGE_SIZE}
              onPageChange={setPage}
              noun="incidentes vencidos"
            />
          )}
        </div>
      )}
    </div>
  );
}
