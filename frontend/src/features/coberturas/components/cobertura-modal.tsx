"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import type { AlcanceOption, Cobertura, CoberturaOperadorOption } from "../types/coberturas";
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
  /** Con cobertura = modo edición (update in-place, mismo id); sin ella, alta. */
  cobertura?: Cobertura | null;
  onClose: () => void;
  onSaved: () => void;
}

/** Alta y edición de una cobertura. La edición es in-place sobre una regla
 * activa/programada (ADR-013, actualización 2026-08-14) — una cancelada es
 * un registro histórico y el backend rechaza editarla. El solapamiento no
 * es un warning como pedía el handoff: el backend lo rechaza con 409, acá
 * se muestra ese error en el banner del modal. */
export function CoberturaModal({
  config,
  operadores,
  alcanceOptions,
  cobertura = null,
  onClose,
  onSaved,
}: CoberturaModalProps) {
  const [ausenteId, setAusenteId] = useState<string | null>(cobertura?.ausenteId ?? null);
  const [reemplazanteId, setReemplazanteId] = useState<string | null>(
    cobertura?.reemplazanteId ?? null,
  );
  const [desde, setDesde] = useState(cobertura?.desde ?? "");
  const [hasta, setHasta] = useState(cobertura?.hasta ?? "");
  const [alcance, setAlcance] = useState<"total" | "parcial">(
    cobertura && !cobertura.alcanceTotal ? "parcial" : "total",
  );
  const [alcanceItems, setAlcanceItems] = useState<string[]>(cobertura?.alcanceItems ?? []);
  const [motivo, setMotivo] = useState(
    cobertura?.motivo && MOTIVOS.includes(cobertura.motivo) ? cobertura.motivo : MOTIVOS[0],
  );
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
    const payload = {
      ausenteId,
      reemplazanteId,
      desde,
      hasta,
      alcanceItems: alcance === "total" ? null : alcanceItems,
      motivo,
    };
    (cobertura ? config.api.update(cobertura.id, payload) : config.api.create(payload))
      .then(onSaved)
      .catch((err: unknown) => {
        console.error("Error al guardar la cobertura:", err);
        setSaveError(
          err instanceof ApiError ? err.message : "No se pudo guardar la cobertura.",
        );
      })
      .finally(() => setSaving(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={cobertura ? "Editar cobertura" : "Nueva cobertura"}
      widthPx={560}
      error={saveError}
    >
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
            // Al editar una cobertura ya vigente, `desde` puede estar en el
            // pasado — el min bloquearía conservarlo.
            min={cobertura ? undefined : hoyIso()}
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
            error={
              alcanceItems.length === 0
                ? `Seleccioná al menos ${config.alcanceItemSingular}.`
                : undefined
            }
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
            {saving ? "Guardando…" : cobertura ? "Guardar cambios" : "Guardar cobertura"}
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
