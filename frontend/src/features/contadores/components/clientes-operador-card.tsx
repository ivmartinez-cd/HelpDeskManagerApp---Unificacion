"use client";

import { Users } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { contadoresApi } from "../api/contadores-api";
import type { OperadorClientes, ResumenClientesOperador } from "../types/calendario";
import { ClienteCruceModal } from "./cliente-cruce-modal";
import { useSession } from "@/services/session-provider";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";

const FALLBACK_COLOR = "#F7941D";

function FilaOperador({ fila, max }: { fila: OperadorClientes; max: number }) {
  const color = fila.operador_color ?? FALLBACK_COLOR;
  return (
    <li className="flex flex-col gap-1">
      <div className="flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5">
          <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: color }} />
          <span className="truncate font-body text-[13px] font-semibold text-foreground">
            {fila.operador_nombre}
          </span>
          {fila.sin_cruce.length > 0 && (
            <span
              className="shrink-0 cursor-help rounded-full bg-amber-500/[0.15] px-1.5 py-0.5 font-body text-[10px] font-semibold text-amber-600"
              title={`Sin cruce con Siges (no suman impresoras):\n${fila.sin_cruce.join("\n")}`}
            >
              {fila.sin_cruce.length} sin cruce
            </span>
          )}
        </span>
        <span className="flex shrink-0 items-baseline gap-2">
          <span className="font-body text-[11px] text-muted-foreground">
            {fila.clientes} {fila.clientes === 1 ? "cliente" : "clientes"}
          </span>
          <span className="font-heading text-[14px] font-extrabold text-foreground">
            {fila.impresoras == null ? "—" : fila.impresoras.toLocaleString("es-AR")}
          </span>
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full"
          style={{
            width: `${max > 0 && fila.impresoras != null ? (fila.impresoras / max) * 100 : 0}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </li>
  );
}

/** Card de Inicio: cartera de clientes de cada operador (calendario de
 * Contadores mirado hacia adelante — el mes en curso subcuenta porque Gestión
 * borra los eventos ya realizados) e impresoras que suman esos clientes
 * (cruce por nombre contra Siges). Si Siges no responde, muestra solo
 * clientes. */
export function ClientesOperadorCard() {
  const { user, modules, can } = useSession();
  const canView = modules.some((m) => m.key === "contadores");
  const canManage = user.isSuperadmin || can("contadores", "manage");

  const [resumen, setResumen] = useState<ResumenClientesOperador | null>(null);
  const [loading, setLoading] = useState<boolean>(canView);
  const [error, setError] = useState<string | null>(null);
  const [resolviendo, setResolviendo] = useState(false);

  const fetchResumen = useCallback(() => {
    contadoresApi
      .getResumenClientesOperador()
      .then(setResumen)
      .catch((err: unknown) => {
        console.error("Error al cargar el resumen de clientes por operador:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar el resumen.");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!canView) return;
    fetchResumen();
  }, [canView, fetchResumen]);

  if (!canView) return null;

  const filas = resumen?.operadores ?? [];
  const max = filas.reduce((m, f) => Math.max(m, f.impresoras ?? 0), 0);
  const sinCruce = [...new Set(filas.flatMap((f) => f.sin_cruce))].sort();

  return (
    <div className="flex w-full flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
          <Users className="h-4 w-4" />
        </span>
        <div className="flex min-w-0 flex-col">
          <h2 className="font-heading text-[14.5px] font-bold text-foreground">
            Contadores por operador
          </h2>
          <span className="truncate font-body text-[12.5px] text-muted-foreground">
            Cartera de clientes e impresoras
          </span>
        </div>
        {resumen && resumen.total_impresoras != null && (
          <span className="ml-auto shrink-0 rounded-full bg-brand-orange/[0.12] px-2 py-0.5 font-body text-[11px] font-semibold text-brand-orange">
            {resumen.total_impresoras.toLocaleString("es-AR")}
          </span>
        )}
      </div>

      {loading ? (
        <div className="flex justify-center py-4">
          <Spinner />
        </div>
      ) : error ? (
        <span className="font-body text-[13px] text-destructive">{error}</span>
      ) : filas.length === 0 ? (
        <span className="font-body text-[13px] text-muted-foreground">
          No hay clientes planificados en el calendario.
        </span>
      ) : (
        <>
          <ul className="flex max-h-80 flex-col gap-2.5 overflow-y-auto">
            {filas.map((fila) => (
              <FilaOperador key={fila.operador_id} fila={fila} max={max} />
            ))}
          </ul>
          {resumen?.total_impresoras == null && (
            <span className="font-body text-[11px] text-amber-600">
              Siges no respondió: se muestran solo los clientes, sin impresoras.
            </span>
          )}
          {sinCruce.length > 0 && (
            <div className="flex items-center justify-between gap-2">
              <span className="font-body text-[11px] text-muted-foreground">
                {sinCruce.length} {sinCruce.length === 1 ? "cliente" : "clientes"} sin cruce
                con Siges — sus impresoras no están sumadas.
              </span>
              {canManage && (
                <button
                  type="button"
                  onClick={() => setResolviendo(true)}
                  className="shrink-0 rounded-full bg-amber-500/[0.15] px-2 py-0.5 font-body text-[11px] font-semibold text-amber-600 hover:bg-amber-500/[0.25]"
                >
                  Resolver
                </button>
              )}
            </div>
          )}
          <Link href="/contadores/calendario" className={cn(brandButtonClasses(), "w-full")}>
            Ver calendario →
          </Link>
        </>
      )}

      {resolviendo && (
        <ClienteCruceModal
          clientes={sinCruce}
          onClose={() => setResolviendo(false)}
          onSaved={fetchResumen}
        />
      )}
    </div>
  );
}
