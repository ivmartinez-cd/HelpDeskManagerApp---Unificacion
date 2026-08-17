"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { GeocodeCandidato, TablaKm } from "../types/liquidaciones";

/** Lista de candidatos de geocode con elección explícita + coords manuales.
 * La elección nunca es automática acá: eso ya lo filtró el backend. */
export function CandidatosPicker({
  candidatos,
  onElegir,
}: {
  candidatos: GeocodeCandidato[];
  onElegir: (body: { candidatoIdx?: number; latitud?: number; longitud?: number }) => Promise<void>;
}) {
  const [manualLat, setManualLat] = useState("");
  const [manualLon, setManualLon] = useState("");
  const [enviando, setEnviando] = useState(false);

  const elegir = async (body: { candidatoIdx?: number; latitud?: number; longitud?: number }) => {
    setEnviando(true);
    try {
      await onElegir(body);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al guardar coordenadas");
    } finally {
      setEnviando(false);
    }
  };

  const manualValida =
    Number.isFinite(parseFloat(manualLat)) && Number.isFinite(parseFloat(manualLon));

  return (
    <div className="flex flex-col gap-2">
      {candidatos.map((c, idx) => (
        <div
          key={`${c.latitud},${c.longitud}`}
          className="flex items-center justify-between gap-3 rounded-[8px] bg-muted/30 px-3 py-2"
        >
          <div className="min-w-0">
            <p className="truncate font-body text-[13px] text-foreground" title={c.formattedAddress}>
              {c.formattedAddress}
            </p>
            <p className="font-body text-[11px] text-muted-foreground tabular-nums">
              {c.latitud.toFixed(6)}, {c.longitud.toFixed(6)} · {c.locationType}
              {c.partialMatch ? " · match parcial" : ""}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <a
              href={`https://www.google.com/maps?q=${c.latitud},${c.longitud}`}
              target="_blank"
              rel="noopener noreferrer"
              className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
            >
              Ver en Maps
            </a>
            <BrandButton size="sm" disabled={enviando} onClick={() => elegir({ candidatoIdx: idx })}>
              Usar
            </BrandButton>
          </div>
        </div>
      ))}
      {candidatos.length === 0 && (
        <p className="font-body text-xs text-muted-foreground italic">
          Google no devolvió candidatos para esta dirección.
        </p>
      )}
      <div className="flex items-end gap-2">
        <BrandInput
          label="Latitud manual"
          value={manualLat}
          placeholder="-38.7189"
          onChange={(e) => setManualLat(e.target.value)}
        />
        <BrandInput
          label="Longitud manual"
          value={manualLon}
          placeholder="-62.2643"
          onChange={(e) => setManualLon(e.target.value)}
        />
        <BrandButton
          size="sm"
          variant="outline"
          disabled={!manualValida || enviando}
          onClick={() =>
            elegir({ latitud: parseFloat(manualLat), longitud: parseFloat(manualLon) })
          }
        >
          Usar manual
        </BrandButton>
      </div>
    </div>
  );
}

/** "Buscar lugar" de una fila de Tabla KM: candidatos del domicilio cargado. */
export function BuscarLugarModal({
  fila,
  onClose,
  onResuelto,
}: {
  fila: TablaKm;
  onClose: () => void;
  onResuelto: (actualizada: TablaKm) => void;
}) {
  const [candidatos, setCandidatos] = useState<GeocodeCandidato[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    liquidacionesApi
      .buscarLugarFila(fila.id)
      .then((r) => setCandidatos(r.candidatos))
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al buscar lugar"));
  }, [fila.id]);

  const handleElegir = async (body: {
    candidatoIdx?: number;
    latitud?: number;
    longitud?: number;
  }) => {
    const actualizada = await liquidacionesApi.resolverCoordenadasFila(fila.id, body);
    toast.success("Coordenadas de la fila guardadas");
    onResuelto(actualizada);
    onClose();
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={`Buscar lugar — ${fila.sucursalNombre}`}
      error={error}
      widthPx={640}
    >
      {!candidatos && !error ? (
        <div className="flex h-32 items-center justify-center">
          <Spinner />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {candidatos && <CandidatosPicker candidatos={candidatos} onElegir={handleElegir} />}
          <div className="flex justify-end">
            <BrandButton variant="outline" onClick={onClose}>
              Cerrar
            </BrandButton>
          </div>
        </div>
      )}
    </BrandModal>
  );
}

