"use client";

import { CalendarioTool } from "@/features/contadores/components/calendario-tool";

export default function CalendarioPage() {
  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold text-brand-charcoal">
          Calendario de Planificación
        </h1>
        <p className="font-body text-sm text-[#8a8a8a]">
          Agenda de clientes y recorridas de tomadores de contadores por operador
        </p>
      </div>
      <CalendarioTool />
    </div>
  );
}
