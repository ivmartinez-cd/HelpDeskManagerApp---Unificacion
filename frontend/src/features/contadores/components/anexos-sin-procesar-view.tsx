"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw, SearchX } from "lucide-react";
import { contadoresApi } from "../api/contadores-api";
import type { AnexoSinProcesar, AnexosSinProcesarResumen } from "../types/calendario";
import { formatDateLocal } from "../utils/calendario-format";
import { AnexosSinProcesarTabla, type OperadorInfo } from "./anexos-sin-procesar-tabla";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";

function KpiCard({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="flex min-w-[120px] flex-col gap-0.5 rounded-[12px] border border-border bg-card px-4 py-3">
      <span className={`font-heading text-2xl font-extrabold tabular-nums ${tone}`}>
        {value}
      </span>
      <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
    </div>
  );
}

function formatConsultadoEn(iso: string): string {
  return new Date(iso).toLocaleString("es-AR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AnexosSinProcesarView() {
  const [rows, setRows] = useState<AnexoSinProcesar[] | null>(null);
  const [resumen, setResumen] = useState<AnexosSinProcesarResumen | null>(null);
  const [operadores, setOperadores] = useState<Record<string, OperadorInfo>>({});
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(() => {
    const today = formatDateLocal(new Date());
    const lista = contadoresApi.listAnexosSinProcesar(today).then(setRows);
    const kpis = contadoresApi.getAnexosSinProcesarResumen(today).then(setResumen);
    const catalogo = contadoresApi.listCalendarioOperadores().then((ops) => {
      setOperadores(
        Object.fromEntries(ops.map((o) => [o.id, { nombre: o.nombre, color: o.color }])),
      );
    });
    return Promise.all([lista, kpis, catalogo])
      .then(() => setError(null))
      .catch((err: unknown) => {
        console.error("Error al cargar anexos sin procesar:", err);
        setError("No se pudo consultar Siges. Reintentá en unos segundos.");
      });
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    void load().finally(() => setRefreshing(false));
  };

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold uppercase tracking-[-.03em] text-foreground">
            Anexos sin procesar
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Clientes con evento vencido en el calendario cuyo anexo todavía no tiene proceso de
            facturación generado en Siges · Solo lectura
          </p>
        </div>
        <div className="flex items-center gap-3">
          {resumen && (
            <span className="font-body text-xs text-muted-foreground">
              Datos de las {formatConsultadoEn(resumen.consultado_en)}
            </span>
          )}
          <BrandButton variant="outline" loading={refreshing} onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4" />
            Actualizar
          </BrandButton>
        </div>
      </div>

      {resumen && (
        <div className="flex flex-wrap gap-3">
          <KpiCard label="Clientes" value={String(resumen.clientes)} tone="text-foreground" />
          <KpiCard
            label="Anexos sin procesar"
            value={String(resumen.anexos)}
            tone={resumen.anexos > 0 ? "text-destructive" : "text-foreground"}
          />
        </div>
      )}

      {rows === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }, (_, i) => (
            <BrandSkeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center justify-between gap-4 rounded-[12px] border border-destructive/20 bg-destructive/10 px-5 py-4">
          <p className="font-body text-sm text-foreground">{error}</p>
          <BrandButton variant="outline" size="sm" onClick={() => void load()}>
            Reintentar
          </BrandButton>
        </div>
      )}

      {rows !== null && !error && (
        <>
          {rows.length === 0 ? (
            <BrandEmptyState
              icon={SearchX}
              title="Sin anexos sin procesar"
              description="Todos los clientes con arrastre en el calendario ya tienen su proceso de facturación generado en Siges."
            />
          ) : (
            <AnexosSinProcesarTabla rows={rows} operadores={operadores} />
          )}

          <p className="font-body text-xs text-muted-foreground">
            {rows.length} {rows.length === 1 ? "anexo" : "anexos"} sin procesar
          </p>

          <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs text-muted-foreground">
            Un anexo cuenta acá cuando su cliente tiene un evento vencido en el calendario de
            Gestión y Siges confirma que el anexo no llegó a tener número de proceso del último
            período ya cerrado (un mes de gracia). Clientes sin cruce contra Siges o anexos sin
            ningún historial de proceso no se muestran: sin certeza, no se acusa a nadie.
          </p>
        </>
      )}
    </div>
  );
}
