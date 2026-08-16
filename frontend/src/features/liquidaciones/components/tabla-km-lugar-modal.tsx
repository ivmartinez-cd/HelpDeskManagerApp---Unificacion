"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  GeocodeCandidato,
  PinSospechoso,
  PrestadorLiquidacion,
  TablaKm,
} from "../types/liquidaciones";

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

/** Pines de Siges cuya distancia al geocode del domicilio supera el umbral.
 * El listado usa solo el cache; "Auditar con Google" geocodifica lo faltante. */
export function PinesSospechososModal({
  prestador,
  onClose,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
}) {
  const [pines, setPines] = useState<PinSospechoso[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [auditando, setAuditando] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    liquidacionesApi
      .listPinesSospechosos(prestador.id)
      .then(setPines)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al listar pines"));
  }, [prestador.id, reloadKey]);

  const handleAuditar = async () => {
    setAuditando(true);
    setError(null);
    try {
      const r = await liquidacionesApi.auditarPines(prestador.id);
      toast.success(
        `Auditoría: ${r.geocodificadas} geocodificadas (${r.llamadasGoogle} llamadas Google)`,
      );
      setReloadKey((k) => k + 1);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al auditar");
    } finally {
      setAuditando(false);
    }
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={`Pines sospechosos — ${prestador.nombreCorto}`}
      error={error}
      widthPx={760}
    >
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          Sucursales cuyo pin de Siges queda a más de 5 km del geocode de su domicilio. El
          listado usa datos ya consultados; &quot;Auditar con Google&quot; geocodifica los
          domicilios que falten (consume llamadas).
        </p>
        {!pines ? (
          <div className="flex h-24 items-center justify-center">
            <Spinner />
          </div>
        ) : pines.length === 0 ? (
          <p className="font-body text-sm text-muted-foreground italic">
            Sin discrepancias mayores al umbral con los datos disponibles.
          </p>
        ) : (
          <div className="flex max-h-[50vh] flex-col gap-2 overflow-y-auto pr-1">
            {pines.map((p) => (
              <div
                key={p.sigesSucursalId}
                className="rounded-[8px] border border-border px-4 py-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="font-body text-sm font-semibold text-foreground">
                    {p.empresaNombre} — {p.sucursalNombre}
                  </p>
                  <Badge variant={p.locationType === "ROOFTOP" ? "danger" : "warning"}>
                    {p.discrepanciaKm.toFixed(1)} km · {p.locationType}
                  </Badge>
                </div>
                <p className="mt-0.5 font-body text-xs text-muted-foreground">{p.direccion}</p>
                <div className="mt-1 flex gap-3 font-body text-[11px] font-bold uppercase tracking-wide">
                  <a
                    href={`https://www.google.com/maps?q=${p.latitudSiges},${p.longitudSiges}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-orange hover:underline"
                  >
                    Pin Siges
                  </a>
                  <a
                    href={`https://www.google.com/maps?q=${p.latitudGeocode},${p.longitudGeocode}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-orange hover:underline"
                  >
                    Geocode
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-3">
          <BrandButton variant="outline" onClick={onClose}>
            Cerrar
          </BrandButton>
          <BrandButton loading={auditando} onClick={handleAuditar}>
            Auditar con Google
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
