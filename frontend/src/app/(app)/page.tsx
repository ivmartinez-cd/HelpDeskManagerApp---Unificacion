import { ClientesOperadorCard } from "@/features/contadores/components/clientes-operador-card";
import { TodayClientsCard } from "@/features/home/components/today-clients-card";
import { ParqueOperadorCard } from "@/features/prestadores/components/parque-operador-card";
import { SlaSummaryCard } from "@/features/sla/components/sla-summary-card";
import { ShiftDashboardCard } from "@/features/turnos/components/shift-dashboard-card";

export const metadata = {
  title: "Inicio",
};

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">Inicio</h1>
        <p className="font-body text-sm text-muted-foreground">
          Panel principal con turnos de operadores y planificación diaria.
        </p>
      </div>

      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-3">
        {/* Turnos Insumos + Turnos ST son tiles compactos de altura fija por
            contenido (franjas horarias del día) — se apilan en su propia
            columna en vez de estirarse a la altura de Clientes/SLA, que son
            widgets más "densos" y crecen con datos reales. */}
        <div className="flex flex-col gap-4">
          <ShiftDashboardCard />
          <ParqueOperadorCard />
        </div>
        <TodayClientsCard />
        <div className="flex flex-col gap-4">
          <SlaSummaryCard />
          <ClientesOperadorCard />
        </div>
      </div>
    </div>
  );
}
