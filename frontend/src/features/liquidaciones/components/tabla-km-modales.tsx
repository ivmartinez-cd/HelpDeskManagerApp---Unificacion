"use client";

import { useState } from "react";
import { toast } from "sonner";
import {
  BrandButton,
  BrandFileInput,
  BrandInput,
  BrandSelect,
} from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PrestadorLiquidacion, Spst, TablaKm } from "../types/liquidaciones";

const FORM_VACIO = { prestadorId: "", spstId: "", empresaNombre: "", sucursalNombre: "", domicilioCliente: "", localidadCliente: "", provinciaCliente: "", kmsRecorrido: "", kmsAFacturar: "", umbralViatico: "30", aplicaViatico: false, urlMaps: "", observaciones: "" };

function entradaAForm(t: TablaKm | null) {
  if (!t) return FORM_VACIO;
  return {
    prestadorId: t.prestadorId,
    spstId: t.spstId ?? "",
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

// El caller lo monta con key={editing?.id ?? "nueva"} para que el estado inicial
// del form se recalcule al cambiar de entrada.
export function EntradaModal({
  isOpen, onClose, prestadores, spsts, editing, onSuccess,
}: {
  isOpen: boolean; onClose: () => void;
  prestadores: PrestadorLiquidacion[]; spsts: Spst[]; editing: TablaKm | null; onSuccess: () => void;
}) {
  const [form, setForm] = useState(() => entradaAForm(editing));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClose = () => { setForm(entradaAForm(editing)); setError(null); onClose(); };
  const filteredSpsts = spsts.filter((s) => !form.prestadorId || s.prestadorId === form.prestadorId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = {
        prestadorId: form.prestadorId,
        spstId: form.spstId || undefined,
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
        <BrandSelect label="Prestador *" required value={form.prestadorId} onChange={(e) => setForm((f) => ({ ...f, prestadorId: e.target.value, spstId: "" }))}>
          <option value="">Seleccioná...</option>
          {prestadores.map((p) => <option key={p.id} value={p.id}>{p.nombreCorto} — {p.nombre}</option>)}
        </BrandSelect>
        <BrandSelect label="SPST (opcional)" value={form.spstId} onChange={(e) => setForm((f) => ({ ...f, spstId: e.target.value }))}>
          <option value="">Sin SPST</option>
          {filteredSpsts.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
        </BrandSelect>
        <BrandInput label="Empresa / Cliente *" required value={form.empresaNombre} onChange={(e) => setForm((f) => ({ ...f, empresaNombre: e.target.value }))} />
        <BrandInput label="Sucursal *" required value={form.sucursalNombre} onChange={(e) => setForm((f) => ({ ...f, sucursalNombre: e.target.value }))} />
        <BrandInput label="Domicilio cliente" value={form.domicilioCliente} onChange={(e) => setForm((f) => ({ ...f, domicilioCliente: e.target.value }))} />
        <BrandInput label="Localidad" value={form.localidadCliente} onChange={(e) => setForm((f) => ({ ...f, localidadCliente: e.target.value }))} />
        <BrandInput label="Provincia" value={form.provinciaCliente} onChange={(e) => setForm((f) => ({ ...f, provinciaCliente: e.target.value }))} />
        <BrandInput label="KMs recorrido *" type="number" step="0.1" required value={form.kmsRecorrido} onChange={(e) => setForm((f) => ({ ...f, kmsRecorrido: e.target.value }))} />
        <BrandInput label="KMs a facturar" type="number" step="0.1" value={form.kmsAFacturar} placeholder="Igual a recorrido si vacío" onChange={(e) => setForm((f) => ({ ...f, kmsAFacturar: e.target.value }))} />
        <BrandInput label="Umbral viático (km)" type="number" step="0.1" value={form.umbralViatico} onChange={(e) => setForm((f) => ({ ...f, umbralViatico: e.target.value }))} />
        <BrandInput label="URL Maps" value={form.urlMaps} placeholder="https://..." onChange={(e) => setForm((f) => ({ ...f, urlMaps: e.target.value }))} />
        <BrandInput label="Observaciones" value={form.observaciones} onChange={(e) => setForm((f) => ({ ...f, observaciones: e.target.value }))} />
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
