"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import type { AlcanceOption, CoberturaOperadorOption } from "../types/coberturas";
import type { CoberturaConfig } from "../lib/config";
import { formatFechaCorta, hoyIso } from "../lib/estado";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";

const MOTIVOS = ["Vacaciones", "Ausencia", "Otro"];

interface CoberturaModalProps {
  config: CoberturaConfig;
  operadores: CoberturaOperadorOption[];
  alcanceOptions: AlcanceOption[];
  onClose: () => void;
  onCreated: () => void;
}

/** Alta de una cobertura. Sin modo edición: el backend no expone update de
 * overrides a propósito (ADR-013 — la única mutación post-alta es cancelar,
 * para no perder el registro de que la regla existió). El handoff preveía
 * "Editar"; se omite hasta que exista el endpoint. El solapamiento tampoco
 * es un warning como pedía el handoff: el backend lo rechaza con 409, acá
 * se muestra ese error en el banner del modal. */
export function CoberturaModal({
  config,
  operadores,
  alcanceOptions,
  onClose,
  onCreated,
}: CoberturaModalProps) {
  const [ausenteId, setAusenteId] = useState<string | null>(null);
  const [reemplazanteId, setReemplazanteId] = useState<string | null>(null);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [alcance, setAlcance] = useState<"total" | "parcial">("total");
  const [alcanceItems, setAlcanceItems] = useState<string[]>([]);
  const [motivo, setMotivo] = useState(MOTIVOS[0]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const rangoInvalido = Boolean(desde && hasta && hasta < desde);
  const completo =
    Boolean(ausenteId && reemplazanteId && desde && hasta) &&
    !rangoInvalido &&
    (alcance === "total" || alcanceItems.length > 0);

  const ausenteNombre =
    operadores.find((o) => o.id === ausenteId)?.nombre ?? "su operador original";

  const opcionesSelect = operadores.map((o) => ({
    id: o.id,
    label: o.nombre,
    sublabel: o.sublabel,
    color: o.color,
  }));

  const handleSubmit = () => {
    if (!completo || !ausenteId || !reemplazanteId) return;
    setSaving(true);
    setSaveError(null);
    config.api
      .create({
        ausenteId,
        reemplazanteId,
        desde,
        hasta,
        alcanceItems: alcance === "total" ? null : alcanceItems,
        motivo,
      })
      .then(onCreated)
      .catch((err: unknown) => {
        console.error("Error al crear la cobertura:", err);
        setSaveError(
          err instanceof ApiError ? err.message : "No se pudo guardar la cobertura.",
        );
      })
      .finally(() => setSaving(false));
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Nueva cobertura" widthPx={560} error={saveError}>
      <p className="-mt-2 mb-5 font-body text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {config.subtitulo}
      </p>

      <div className="flex flex-col gap-4">
        <SearchableSelect
          label="¿Quién falta?"
          options={opcionesSelect}
          value={ausenteId}
          onChange={setAusenteId}
          placeholder="Buscá operador…"
        />
        <SearchableSelect
          label="¿Quién lo cubre?"
          options={opcionesSelect}
          value={reemplazanteId}
          onChange={setReemplazanteId}
          exclude={ausenteId ? [ausenteId] : undefined}
          placeholder="Buscá operador…"
        />

        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Desde"
            type="date"
            value={desde}
            min={hoyIso()}
            onChange={(e) => setDesde(e.target.value)}
          />
          <BrandInput
            label="Hasta"
            type="date"
            value={hasta}
            min={desde || hoyIso()}
            onChange={(e) => setHasta(e.target.value)}
          />
        </div>
        {rangoInvalido && (
          <p role="alert" className="-mt-2 font-body text-xs text-destructive">
            La fecha de fin tiene que ser posterior al inicio.
          </p>
        )}

        <div className="flex flex-col gap-1.5">
          <span className="font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
            Alcance
          </span>
          <SegmentedControl
            label="Alcance"
            options={[
              { value: "total", label: "Total" },
              { value: "parcial", label: config.alcanceParcialLabel },
            ]}
            value={alcance}
            onChange={(v) => setAlcance(v as "total" | "parcial")}
          />
          {alcance === "total" && (
            <p className="font-body text-xs text-muted-foreground">{config.alcanceTotalHint}</p>
          )}
        </div>

        {alcance === "parcial" && (
          <SearchableSelect
            label={config.multiLabel}
            options={alcanceOptions.map((o) => ({ id: o.id, label: o.label }))}
            multiple
            value={alcanceItems}
            onChange={setAlcanceItems}
            allowCustom={config.multiAllowCustom}
            placeholder={config.multiPlaceholder}
            error={alcanceItems.length === 0 ? `Seleccioná al menos un ${config.alcanceUnidad === "PST" ? "PST" : "cliente"}.` : undefined}
          />
        )}

        <BrandSelect label="Motivo" value={motivo} onChange={(e) => setMotivo(e.target.value)}>
          {MOTIVOS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </BrandSelect>

        <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs leading-relaxed text-muted-foreground">
          {config.notaVuelta(hasta ? formatFechaCorta(hasta) : "…", ausenteNombre)}
        </p>

        <div className="flex justify-end gap-2 pt-1">
          <BrandButton variant="outline" onClick={onClose}>
            Cancelar
          </BrandButton>
          <BrandButton onClick={handleSubmit} disabled={!completo} loading={saving}>
            {saving ? "Guardando…" : "Guardar cobertura"}
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
