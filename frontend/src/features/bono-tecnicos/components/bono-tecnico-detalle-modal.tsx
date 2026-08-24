"use client";

import { useBonoTecnicoDetalle } from "../hooks/use-bono-tecnico-detalle";
import { CATEGORIAS, type IncidenteBono } from "../types/bono-tecnicos";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";

function IncidentesSection({
  label,
  incidentes,
}: {
  label: string;
  incidentes: IncidenteBono[];
}) {
  return (
    <section className="flex flex-col gap-2">
      <h3 className="font-body text-[11px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        {label} ({incidentes.length})
      </h3>
      {incidentes.length === 0 ? (
        <p className="font-body text-xs text-muted-foreground">Sin incidentes en el período.</p>
      ) : (
        <div className="overflow-x-auto thin-scrollbar rounded-[8px] border border-border">
          <table className="w-full border-collapse font-body text-xs">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="whitespace-nowrap px-3 py-1.5 font-semibold">ID</th>
                <th className="px-3 py-1.5 font-semibold">Cliente</th>
                <th className="px-3 py-1.5 font-semibold">Sucursal</th>
                <th className="px-3 py-1.5 font-semibold">Nro. Serie</th>
              </tr>
            </thead>
            <tbody>
              {incidentes.map((i) => (
                <tr key={i.id_incidente} className="border-b border-border/50 last:border-b-0">
                  <td className="whitespace-nowrap px-3 py-1.5 tabular-nums">{i.id_incidente}</td>
                  <td className="px-3 py-1.5">{i.cliente}</td>
                  <td className="px-3 py-1.5">{i.sucursal}</td>
                  <td className="px-3 py-1.5">{i.nro_serie}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function BonoTecnicoDetalleModal({
  tecnico,
  periodo,
  idTecnico,
  onClose,
}: {
  tecnico: string;
  periodo: string;
  idTecnico: number;
  onClose: () => void;
}) {
  const { incidentes, loading, error } = useBonoTecnicoDetalle(periodo, idTecnico);
  const porCategoria = (categoria: string) => incidentes.filter((i) => i.categoria === categoria);

  return (
    <BrandModal isOpen title={tecnico} onClose={onClose} widthPx={720} error={error ?? undefined}>
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <Spinner />
        </div>
      ) : (
        <div className="flex max-h-[70vh] flex-col gap-5 overflow-y-auto thin-scrollbar pr-1">
          {CATEGORIAS.map((c) => (
            <IncidentesSection key={c.key} label={c.label} incidentes={porCategoria(c.key)} />
          ))}
        </div>
      )}
    </BrandModal>
  );
}
