"use client";

import { CalendarDays } from "lucide-react";
import Link from "next/link";
import { DashboardCard } from "@/features/home/components/dashboard-card";
import type { ProximosEquipo } from "@/features/home/hooks/use-inicio-data";
import { formatRango, iniciales } from "../lib/fechas";

const TOP_LISTA = 6;

interface Item {
  id: string;
  tipo: "vacacion" | "home_office";
  nombre: string;
  color: string;
  startDate: string;
  endDate: string;
}

function armarLista({ vacaciones, homeOffice }: ProximosEquipo): Item[] {
  const items: Item[] = [
    ...vacaciones.map((s) => ({
      id: s.id,
      tipo: "vacacion" as const,
      nombre: s.empleadoNombre,
      color: s.empleadoColor,
      startDate: s.startDate,
      endDate: s.endDate,
    })),
    ...homeOffice.map((a) => ({
      id: a.id,
      tipo: "home_office" as const,
      nombre: a.empleadoNombre,
      color: a.empleadoColor,
      startDate: a.startDate,
      endDate: a.endDate,
    })),
  ];
  return items.sort((a, b) => a.startDate.localeCompare(b.startDate));
}

export function ProximosEquipoCard({
  data,
  loading,
  error,
}: {
  data: ProximosEquipo | null;
  loading: boolean;
  error: string | null;
}) {
  const items = data ? armarLista(data) : [];

  return (
    <DashboardCard
      icon={CalendarDays}
      title="Próximos días del equipo"
      subtitle="Vacaciones y home office · próximas 3 semanas"
      loading={loading}
      error={error}
      headerRight={
        !loading && !error && items.length > 0 ? (
          <span className="shrink-0 rounded-full bg-brand-orange/15 px-2.5 py-0.5 font-heading text-[12px] font-bold text-brand-orange">
            {items.length}
          </span>
        ) : undefined
      }
    >
      {items.length === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay vacaciones ni home office agendados en las próximas semanas.
        </span>
      ) : (
        <div className="mt-2.5 flex flex-col gap-1.5 border-t border-border/60 pt-2.5">
          {items.slice(0, TOP_LISTA).map((item) => (
            <div key={`${item.tipo}-${item.id}`} className="flex items-center gap-2.5">
              <span
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-heading text-[9.5px] font-bold text-white"
                style={{ backgroundColor: item.color }}
              >
                {iniciales(item.nombre)}
              </span>
              <span className="flex-1 truncate font-body text-[12.5px] font-semibold text-foreground/75">
                {item.nombre}
              </span>
              <span className="shrink-0 font-body text-[11px] font-semibold text-muted-foreground">
                {item.tipo === "home_office" ? "Home office" : "Vacaciones"} · {formatRango(item.startDate, item.endDate)}
              </span>
            </div>
          ))}
          <Link
            href="/vacaciones"
            className="mt-1 font-body text-[12.5px] font-bold text-brand-orange hover:text-brand-orange-hover"
          >
            Ver en Vacaciones →
          </Link>
        </div>
      )}
    </DashboardCard>
  );
}
