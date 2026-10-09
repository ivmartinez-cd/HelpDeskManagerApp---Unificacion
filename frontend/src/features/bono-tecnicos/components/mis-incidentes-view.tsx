"use client";

import { useState } from "react";
import { IncidentesCategoriaSection } from "./incidentes-categoria-section";
import { useMisIncidentes } from "../hooks/use-mis-incidentes";
import { CATEGORIAS } from "../types/bono-tecnicos";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { Spinner } from "@/shared/components/ui/spinner";
import { todayInArg } from "@/shared/utils/date-arg";

/** Servicio Técnico > Técnicos > Mis incidentes: lo que el técnico
 * autenticado lleva cerrado en el mes (por defecto el actual, con selector
 * para los anteriores), por categoría del bono. Mismos incidentes que ve
 * gerencia en el detalle de Bono Técnicos para ese técnico. */
export function MisIncidentesView() {
  const mesActual = todayInArg().slice(0, 7);
  const [monthValue, setMonthValue] = useState(mesActual);
  const { incidentes, vinculado, loading, error } = useMisIncidentes(monthValue);
  const porCategoria = (categoria: string) => incidentes.filter((i) => i.categoria === categoria);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">Mis incidentes</h1>
          <p className="font-body text-sm text-muted-foreground">
            Incidentes cerrados a tu nombre en Siges durante el mes elegido.
          </p>
        </div>
        <label className="flex flex-col gap-1">
          <span className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
            Mes
          </span>
          <input
            type="month"
            value={monthValue}
            max={mesActual}
            onChange={(e) => setMonthValue(e.target.value || mesActual)}
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

      {!loading && !error && vinculado === false && (
        <p className="rounded-[12px] border border-border bg-card px-6 py-5 font-body text-sm text-muted-foreground">
          Tu usuario no está vinculado a un técnico de Siges. Pedí que te vinculen desde Gestión de
          Personal.
        </p>
      )}

      {!loading && !error && vinculado && (
        <div className="flex flex-col gap-6">
          <KpiGrid className="lg:grid-cols-6">
            <KpiTile label="Total" value={String(incidentes.length)} tone="neutral" />
            {CATEGORIAS.map((c) => (
              <KpiTile key={c.key} label={c.label} value={String(porCategoria(c.key).length)} />
            ))}
          </KpiGrid>
          {CATEGORIAS.map((c) => (
            <IncidentesCategoriaSection
              key={c.key}
              label={c.label}
              incidentes={porCategoria(c.key)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
