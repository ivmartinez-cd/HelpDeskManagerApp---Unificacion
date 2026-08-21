"use client";

import { Download } from "lucide-react";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { hoyIso } from "../../lib/variante-estado";

interface Props {
  esEdicion: boolean;
  opcionesAusente: { id: string; label: string }[];
  ausenteId: string | null;
  setAusenteId: (id: string | null) => void;
  desde: string;
  setDesde: (v: string) => void;
  hasta: string;
  setHasta: (v: string) => void;
  rangoInvalido: boolean;
  precargar: () => void;
  precargando: boolean;
  motivo: string;
  setMotivo: (v: string) => void;
  origenTexto: string;
  setOrigenTexto: (v: string) => void;
}

/** Fila "¿Quién falta? / Desde / Hasta / Precargar" + "Motivo / Origen" del
 * editor de grilla de vacaciones, extraída de `variante-editor.tsx` porque
 * ese archivo ya superaba el tamaño máximo de archivo (§4). */
export function VarianteIdentificacionFields({
  esEdicion, opcionesAusente, ausenteId, setAusenteId, desde, setDesde, hasta, setHasta,
  rangoInvalido, precargar, precargando, motivo, setMotivo, origenTexto, setOrigenTexto,
}: Props) {
  return (
    <>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_160px_160px_auto]">
        <SearchableSelect
          label="¿Quién falta?"
          options={opcionesAusente}
          value={ausenteId}
          onChange={setAusenteId}
          placeholder="Buscá operador…"
          disabled={esEdicion}
        />
        <BrandInput
          label="Desde"
          type="date"
          value={desde}
          min={esEdicion ? undefined : hoyIso()}
          onChange={(e) => setDesde(e.target.value)}
        />
        <BrandInput
          label="Hasta"
          type="date"
          value={hasta}
          min={desde || hoyIso()}
          onChange={(e) => setHasta(e.target.value)}
        />
        <div className="flex items-end">
          <BrandButton
            type="button"
            variant="outline"
            onClick={precargar}
            loading={precargando}
            disabled={!ausenteId || !desde || !hasta || rangoInvalido}
            title="Trae la grilla titular con las franjas del ausente marcadas como huecos a resolver"
          >
            <Download className="h-4 w-4" />
            Precargar
          </BrandButton>
        </div>
      </div>
      {rangoInvalido && (
        <p className="font-body text-xs text-destructive">La fecha de fin es anterior a la de inicio.</p>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <BrandInput
          label="Motivo"
          value={motivo}
          maxLength={200}
          placeholder="Vacaciones M. J. Vela"
          onChange={(e) => setMotivo(e.target.value)}
        />
        <BrandInput
          label="Origen (opcional)"
          value={origenTexto}
          maxLength={200}
          placeholder="Solicitud de vacaciones aprobada el 20/08"
          hint="Texto libre para trazabilidad; no enlaza con Gestión de Personal."
          onChange={(e) => setOrigenTexto(e.target.value)}
        />
      </div>
    </>
  );
}
