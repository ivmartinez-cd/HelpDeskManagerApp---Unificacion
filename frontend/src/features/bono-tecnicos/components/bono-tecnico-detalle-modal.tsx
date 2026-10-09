"use client";

import { IncidentesCategoriaSection } from "./incidentes-categoria-section";
import { useBonoTecnicoDetalle } from "../hooks/use-bono-tecnico-detalle";
import { CATEGORIAS } from "../types/bono-tecnicos";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";

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
            <IncidentesCategoriaSection
              key={c.key}
              label={c.label}
              incidentes={porCategoria(c.key)}
            />
          ))}
        </div>
      )}
    </BrandModal>
  );
}
