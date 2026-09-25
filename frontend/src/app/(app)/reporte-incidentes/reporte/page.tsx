import { Suspense } from "react";
import { ReporteDashboard } from "@/features/reporte-incidentes/components/dashboard/reporte-dashboard";

export const metadata = {
  title: "Reporte de incidentes",
};

export default function ReporteIncidentesDashboardPage() {
  // useSearchParams exige un límite de Suspense en páginas prerenderizables.
  return (
    <Suspense>
      <ReporteDashboard />
    </Suspense>
  );
}
