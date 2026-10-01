"use client";

import { CalendarDays } from "lucide-react";
import { DashboardCard } from "@/shared/components/dashboard/dashboard-card";
import { CardEmpty, CardLink, CountBadge } from "@/shared/components/dashboard/dashboard-card-bits";
import type { ProximosEquipo } from "../types/vacaciones";
import { formatRango, iniciales } from "../lib/fechas";
import type { Ausencia } from "../types/vacaciones";

interface Item {
  id: string;
  tipo: "vacacion" | "home_office" | "baja";
  nombre: string;
  color: string;
  startDate: string;
  endDate: string;
}

const ETIQUETA: Record<Item["tipo"], string> = {
  vacacion: "Vacaciones",
  home_office: "Home office",
  baja: "Baja por enfermedad",
};

function ausenciaItem(a: Ausencia, tipo: Item["tipo"]): Item {
  return {
    id: a.id,
    tipo,
    nombre: a.empleadoNombre,
    color: a.empleadoColor,
    startDate: a.startDate,
    endDate: a.endDate,
  };
}

function armarLista({ vacaciones, homeOffice, bajas }: ProximosEquipo): Item[] {
  const items: Item[] = [
    ...vacaciones.map((s) => ({
      id: s.id,
      tipo: "vacacion" as const,
      nombre: s.empleadoNombre,
      color: s.empleadoColor,
      startDate: s.startDate,
      endDate: s.endDate,
    })),
    ...homeOffice.map((a) => ausenciaItem(a, "home_office")),
    ...bajas.map((a) => ausenciaItem(a, "baja")),
  ];
  return items.sort((a, b) => a.startDate.localeCompare(b.startDate));
}

export function ProximosEquipoCard({
  data,
  loading,
  error,
  onRetry,
}: {
  data: ProximosEquipo | null;
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}) {
  const items = data ? armarLista(data) : [];

  return (
    <DashboardCard
      icon={CalendarDays}
      title="Equipo"
      subtitle="Vacaciones, home office y bajas · 3 semanas"
      loading={loading}
      error={error}
      onRetry={onRetry}
      headerRight={items.length > 0 ? <CountBadge value={items.length} tone="brand" /> : undefined}
      footer={<CardLink href="/vacaciones">Ver en Vacaciones →</CardLink>}
    >
      {items.length === 0 ? (
        <CardEmpty>Nada agendado en las próximas semanas.</CardEmpty>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {items.map((item) => (
            <li key={`${item.tipo}-${item.id}`} className="flex items-center gap-2">
              <span
                className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full font-heading text-[9.5px] font-bold text-white"
                style={{ backgroundColor: item.color }}
              >
                {iniciales(item.nombre)}
              </span>
              <span className="min-w-0 flex-1 leading-tight">
                <span className="block truncate font-body text-[12.5px] font-semibold text-foreground/80">
                  {item.nombre}
                </span>
                <span className="block truncate font-body text-[11px] text-muted-foreground">
                  {ETIQUETA[item.tipo]} · {formatRango(item.startDate, item.endDate)}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </DashboardCard>
  );
}
