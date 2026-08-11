import { TodayClientsCard } from "@/features/home/components/today-clients-card";
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

      <div className="flex flex-wrap gap-4">
        <ShiftDashboardCard />
        <TodayClientsCard />
      </div>
    </div>
  );
}
