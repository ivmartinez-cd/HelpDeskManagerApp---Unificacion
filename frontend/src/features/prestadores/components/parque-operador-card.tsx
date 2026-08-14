"use client";

import { Printer } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import { prestadoresApi } from "../api/prestadores-api";
import type { PrestadoresResumen } from "../types/prestadores";
import { useSession } from "@/services/session-provider";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";

const FALLBACK_COLOR = "#F7941D";

interface ParqueOperador {
  operadorId: string | null;
  nombre: string;
  color: string | null;
  equipos: number;
  prestadores: number;
}

/** Suma el parque (equipos de los PST activos) por operador, a partir del
 * resumen agrupado que ya arma el backend — el conteo de equipos viene en
 * vivo desde Siges. "Sin asignar" va al final; el resto, de mayor a menor. */
function agruparParque(resumen: PrestadoresResumen): ParqueOperador[] {
  const filas = resumen.grupos.flatMap((grupo) => {
    const activos = grupo.prestadores.filter((p) => p.isActive);
    if (activos.length === 0) return [];
    return [
      {
        operadorId: grupo.operadorId,
        nombre: grupo.operadorNombre ?? "Sin asignar",
        color: grupo.operadorColor,
        equipos: activos.reduce((sum, p) => sum + (p.equipos ?? 0), 0),
        prestadores: activos.length,
      },
    ];
  });
  return filas.sort((a, b) => {
    if (a.operadorId === null) return 1;
    if (b.operadorId === null) return -1;
    return b.equipos - a.equipos;
  });
}

function FilaOperador({ fila, max }: { fila: ParqueOperador; max: number }) {
  const color = fila.color ?? FALLBACK_COLOR;
  return (
    <li className="flex flex-col gap-1">
      <div className="flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5">
          <span
            className="h-2 w-2 shrink-0 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="truncate font-body text-[13px] font-semibold text-foreground">
            {fila.nombre}
          </span>
          <span className="shrink-0 font-body text-[11px] text-muted-foreground">
            {fila.prestadores} PST
          </span>
        </span>
        <span className="shrink-0 font-heading text-[14px] font-extrabold text-foreground">
          {fila.equipos.toLocaleString("es-AR")}
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full"
          style={{
            width: `${max > 0 ? (fila.equipos / max) * 100 : 0}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </li>
  );
}

/** Card de Inicio: parque de impresoras a cargo de cada operador (suma de los
 * equipos de sus PST activos, contados en vivo desde Siges). */
export function ParqueOperadorCard() {
  const { modules } = useSession();
  const canView = modules.some((m) => m.key === "prestadores");

  const [resumen, setResumen] = useState<PrestadoresResumen | null>(null);
  const [loading, setLoading] = useState<boolean>(canView);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!canView) return;
    prestadoresApi
      .getResumen()
      .then(setResumen)
      .catch((err: unknown) => {
        console.error("Error al cargar el parque por operador:", err);
        setError(err instanceof Error ? err.message : "No se pudo cargar el parque.");
      })
      .finally(() => setLoading(false));
  }, [canView]);

  if (!canView) return null;

  const filas = resumen ? agruparParque(resumen) : [];
  const total = filas.reduce((sum, f) => sum + f.equipos, 0);
  const max = filas.reduce((m, f) => Math.max(m, f.equipos), 0);

  return (
    <div className="flex w-full flex-col gap-3 rounded-[12px] border border-border bg-card p-5">
      <div className="flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
          <Printer className="h-4 w-4" />
        </span>
        <div className="flex min-w-0 flex-col">
          <h2 className="font-heading text-[14.5px] font-bold text-foreground">
            Parque por operador
          </h2>
          <span className="truncate font-body text-[12.5px] text-muted-foreground">
            Impresoras de los PST asignados
          </span>
        </div>
        {total > 0 && (
          <span className="ml-auto shrink-0 rounded-full bg-brand-orange/[0.12] px-2 py-0.5 font-body text-[11px] font-semibold text-brand-orange">
            {total.toLocaleString("es-AR")}
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
          No hay prestadores activos cargados.
        </span>
      ) : (
        <>
          <ul className="flex max-h-80 flex-col gap-2.5 overflow-y-auto">
            {filas.map((fila) => (
              <FilaOperador key={fila.operadorId ?? "sin-asignar"} fila={fila} max={max} />
            ))}
          </ul>
          <Link href="/prestadores" className={cn(brandButtonClasses(), "w-full")}>
            Ver prestadores →
          </Link>
        </>
      )}
    </div>
  );
}
