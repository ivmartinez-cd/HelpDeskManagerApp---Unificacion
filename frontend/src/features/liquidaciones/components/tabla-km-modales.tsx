"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandSelect,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, TablaKm } from "../types/liquidaciones";
import { BuscarLugarModal } from "./tabla-km-lugar-modal";

// Prefill del alta asistida desde Siges (ADR-014 DS3) — solo datos descriptivos,
// el km queda vacío a propósito: es dato manual del acuerdo comercial.
export interface PlantillaEntrada {
  empresaNombre: string;
  sucursalNombre: string;
  domicilioCliente: string;
  localidadCliente: string;
  provinciaCliente: string;
}

function entradaAForm(
  t: TablaKm | null,
  defaultPrestadorId: string,
  plantilla: PlantillaEntrada | null,
) {
  if (!t) return { prestadorId: defaultPrestadorId, empresaNombre: "", sucursalNombre: "", domicilioCliente: "", localidadCliente: "", provinciaCliente: "", kmsRecorrido: "", kmsAFacturar: "", umbralViatico: "30", aplicaViatico: false, urlMaps: "", observaciones: "", ...plantilla };
  return {
    prestadorId: t.prestadorId,
    empresaNombre: t.empresaNombre,
    sucursalNombre: t.sucursalNombre,
    domicilioCliente: t.domicilioCliente ?? "",
    localidadCliente: t.localidadCliente ?? "",
    provinciaCliente: t.provinciaCliente ?? "",
    kmsRecorrido: String(t.kmsRecorrido),
    kmsAFacturar: String(t.kmsAFacturar),
    umbralViatico: String(t.umbralViatico),
    aplicaViatico: t.aplicaViatico,
    urlMaps: t.urlMaps ?? "",
    observaciones: t.observaciones ?? "",
  };
}

const LABEL_COORDS_ORIGEN: Record<string, string> = {
  siges: "Siges",
  geocode: "Geocodificado",
  manual: "Manual",
};

// El caller lo monta con key={editing?.id ?? "nueva"} para que el estado inicial
// del form se recalcule al cambiar de entrada.
export function EntradaModal({
  isOpen, onClose, prestadores, editing, defaultPrestadorId, onSuccess, plantilla = null,
}: {
  isOpen: boolean; onClose: () => void;
  prestadores: PrestadorLiquidacion[]; editing: TablaKm | null; defaultPrestadorId: string; onSuccess: () => void;
  plantilla?: PlantillaEntrada | null;
}) {
  const [form, setForm] = useState(() => entradaAForm(editing, defaultPrestadorId, plantilla));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [buscarLugarOpen, setBuscarLugarOpen] = useState(false);
  const [recalculando, setRecalculando] = useState(false);

  const handleClose = () => { setForm(entradaAForm(editing, defaultPrestadorId, plantilla)); setError(null); onClose(); };

  // Recalcula ida+vuelta reales contra Google usando las coords guardadas de la
  // fila (2 llamadas). El resultado pisa km/viático pero nunca umbral ni
  // observaciones — la fila se refresca vía onSuccess y se cierra el modal.
  const handleRecalcular = async () => {
    if (!editing) return;
    setRecalculando(true);
    setError(null);
    try {
      const actualizada = await liquidacionesApi.recalcularKmFila(editing.id);
      toast.success(
        `KM recalculados: ida ${actualizada.kmsIda?.toFixed(1)} + vuelta ${actualizada.kmsVuelta?.toFixed(1)} = ${actualizada.kmsRecorrido.toFixed(1)} km`,
      );
      onSuccess();
      handleClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al recalcular");
    } finally {
      setRecalculando(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = {
        prestadorId: form.prestadorId,
        empresaNombre: form.empresaNombre,
        sucursalNombre: form.sucursalNombre,
        domicilioCliente: form.domicilioCliente || undefined,
        localidadCliente: form.localidadCliente || undefined,
        provinciaCliente: form.provinciaCliente || undefined,
        kmsRecorrido: parseFloat(form.kmsRecorrido),
        kmsAFacturar: parseFloat(form.kmsAFacturar) || parseFloat(form.kmsRecorrido),
        umbralViatico: parseFloat(form.umbralViatico),
        aplicaViatico: form.aplicaViatico,
        urlMaps: form.urlMaps || undefined,
        observaciones: form.observaciones || undefined,
      };
      if (editing) {
        await liquidacionesApi.updateTablaKm(editing.id, body);
        toast.success("Entrada actualizada");
      } else {
        await liquidacionesApi.createTablaKm(body);
        toast.success("Entrada creada");
      }
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title={editing ? "Editar entrada Tabla KM" : "Nueva entrada Tabla KM"} error={error} widthPx={580}>
      <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4">
        <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value }))}>
          <option value="">Seleccioná...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
        </BrandSelect>
        <BrandInput label="Empresa / Cliente *" required value={form.empresaNombre} onChange={(e) => setForm((f) => ({ ...f, empresaNombre: e.target.value }))} />
        <BrandInput label="Sucursal *" required value={form.sucursalNombre} onChange={(e) => setForm((f) => ({ ...f, sucursalNombre: e.target.value }))} />
        <BrandInput label="Domicilio cliente" value={form.domicilioCliente} onChange={(e) => setForm((f) => ({ ...f, domicilioCliente: e.target.value }))} />
        <BrandInput label="Localidad" value={form.localidadCliente} onChange={(e) => setForm((f) => ({ ...f, localidadCliente: e.target.value }))} />
        <BrandInput label="Provincia" value={form.provinciaCliente} onChange={(e) => setForm((f) => ({ ...f, provinciaCliente: e.target.value }))} />
        <BrandInput label="KMs recorrido *" type="number" step="0.1" required value={form.kmsRecorrido} hint="Total del viaje: ida + vuelta." onChange={(e) => setForm((f) => ({ ...f, kmsRecorrido: e.target.value }))} />
        <BrandInput label="KMs a facturar" type="number" step="0.1" value={form.kmsAFacturar} placeholder="Igual a recorrido si vacío" hint="Puede ser menor si aplica franquicia." onChange={(e) => setForm((f) => ({ ...f, kmsAFacturar: e.target.value }))} />
        <BrandInput label="Umbral viático (km)" type="number" step="0.1" value={form.umbralViatico} hint="Si el total supera este valor, aplica viático. Default: 30 km." onChange={(e) => setForm((f) => ({ ...f, umbralViatico: e.target.value }))} />
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">URL Maps</span>
            {form.urlMaps && (
              <a href={form.urlMaps} target="_blank" rel="noopener noreferrer" className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline">
                Abrir en Maps →
              </a>
            )}
          </div>
          <input
            value={form.urlMaps}
            placeholder="https://..."
            onChange={(e) => setForm((f) => ({ ...f, urlMaps: e.target.value }))}
            className="rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40"
          />
        </div>
        <BrandInput label="Observaciones" value={form.observaciones} onChange={(e) => setForm((f) => ({ ...f, observaciones: e.target.value }))} />
        {editing && (
          <div className="col-span-2 flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">Coordenadas destino</span>
                {editing.coordsOrigen && (
                  <Badge variant={editing.coordsOrigen === "siges" ? "neutral" : "info"}>
                    {LABEL_COORDS_ORIGEN[editing.coordsOrigen] ?? editing.coordsOrigen}
                  </Badge>
                )}
              </div>
              {editing.latitudDestino != null && editing.longitudDestino != null && (
                <a
                  href={`https://www.google.com/maps?q=${editing.latitudDestino},${editing.longitudDestino}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
                >
                  Ver pin →
                </a>
              )}
            </div>
            <p className="font-body text-sm text-muted-foreground tabular-nums">
              {editing.latitudDestino != null && editing.longitudDestino != null
                ? `${editing.latitudDestino.toFixed(6)}, ${editing.longitudDestino.toFixed(6)}`
                : "Sin coordenadas — usá Buscar lugar o cargalas a mano"}
              {editing.geocodeFormattedAddress ? ` · ${editing.geocodeFormattedAddress}` : ""}
            </p>
            {editing.kmsIda != null && editing.kmsVuelta != null && (
              <p className="font-body text-xs text-muted-foreground tabular-nums">
                Ida {editing.kmsIda.toFixed(1)} km · Vuelta {editing.kmsVuelta.toFixed(1)} km ·
                Total {(editing.kmsIda + editing.kmsVuelta).toFixed(1)} km
              </p>
            )}
            <div className="flex gap-2 pt-1">
              <BrandButton type="button" size="sm" variant="outline" onClick={() => setBuscarLugarOpen(true)}>
                Buscar lugar
              </BrandButton>
              {editing.latitudDestino != null && editing.longitudDestino != null && (
                <BrandButton type="button" size="sm" variant="outline" loading={recalculando} onClick={handleRecalcular}>
                  Recalcular KM (ida y vuelta)
                </BrandButton>
              )}
            </div>
          </div>
        )}
        <div className="col-span-2 flex items-center gap-3">
          <label className="flex items-center gap-2 font-body text-sm text-muted-foreground cursor-pointer">
            <input type="checkbox" checked={form.aplicaViatico} onChange={(e) => setForm((f) => ({ ...f, aplicaViatico: e.target.checked }))} className="accent-brand-orange" />
            Aplica viático
          </label>
        </div>
        <div className="col-span-2 flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={handleClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={loading}>Guardar</BrandButton>
        </div>
      </form>
      {buscarLugarOpen && editing && (
        <BuscarLugarModal
          fila={editing}
          onClose={() => setBuscarLugarOpen(false)}
          onResuelto={() => { onSuccess(); handleClose(); }}
        />
      )}
    </BrandModal>
  );
}

export function CsvImportModal({ isOpen, onClose, onSuccess }: { isOpen: boolean; onClose: () => void; onSuccess: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const handleClose = () => { setFile(null); setError(null); onClose(); };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await liquidacionesApi.importTablaKmCsv(file);
      toast.success(`${res.creados} entradas importadas`);
      handleClose();
      onSuccess();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al importar");
    } finally {
      setLoading(false);
    }
  };
  return (
    <BrandModal isOpen={isOpen} onClose={handleClose} title="Cargar planilla CSV" error={error}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <BrandFileInput label="Archivo CSV *" accept=".csv" required onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <div className="flex justify-end gap-3 pt-1">
          <BrandButton type="button" variant="outline" onClick={handleClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={loading} disabled={!file}>Importar</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
