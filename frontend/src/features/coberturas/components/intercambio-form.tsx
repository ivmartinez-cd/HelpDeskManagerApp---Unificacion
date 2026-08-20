"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import type {
  AlcanceOption,
  CoberturaOperadorOption,
  Intercambio,
  IntercambioPayload,
  IntercambiosApi,
} from "../types/coberturas";
import { formatFechaCorta, hoyIso } from "../lib/estado";
import { intercambioAPayload } from "../lib/intercambios";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { SearchableSelect } from "@/shared/components/ui/searchable-select";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";

interface IntercambioFormProps {
  api: IntercambiosApi;
  operadores: CoberturaOperadorOption[];
  alcanceOptions: AlcanceOption[];
  /** Con intercambio = edición in-place del par (mismo id); sin él, alta. */
  intercambio?: Intercambio | null;
  onError: (mensaje: string | null) => void;
  onClose: () => void;
  onSaved: () => void;
}

/** Cuerpo del modal en modo Intercambio (ADR-026): A toma las franjas de B
 * y B las de A durante el rango. Alcance Total = todas las franjas de cada
 * uno; "Franjas específicas" = un selector por lado. El backend crea las dos
 * coberturas cruzadas en una transacción y rechaza solapes con 409, que se
 * muestra en el banner del modal vía `onError`. */
export function IntercambioForm({
  api,
  operadores,
  alcanceOptions,
  intercambio = null,
  onError,
  onClose,
  onSaved,
}: IntercambioFormProps) {
  const inicial = intercambio ? intercambioAPayload(intercambio) : null;
  const [operadorAId, setOperadorAId] = useState<string | null>(inicial?.operadorAId ?? null);
  const [operadorBId, setOperadorBId] = useState<string | null>(inicial?.operadorBId ?? null);
  const [desde, setDesde] = useState(inicial?.desde ?? "");
  const [hasta, setHasta] = useState(inicial?.hasta ?? "");
  const [alcance, setAlcance] = useState<"total" | "parcial">(
    inicial && (inicial.alcanceItemsA || inicial.alcanceItemsB) ? "parcial" : "total",
  );
  const [franjasA, setFranjasA] = useState<string[]>(inicial?.alcanceItemsA ?? []);
  const [franjasB, setFranjasB] = useState<string[]>(inicial?.alcanceItemsB ?? []);
  const [motivo, setMotivo] = useState(inicial?.motivo ?? "");
  const [saving, setSaving] = useState(false);

  const rangoInvalido = Boolean(desde && hasta && hasta < desde);
  const completo =
    Boolean(operadorAId && operadorBId && desde && hasta) &&
    !rangoInvalido &&
    (alcance === "total" || (franjasA.length > 0 && franjasB.length > 0));

  const nombreDe = (id: string | null) =>
    operadores.find((o) => o.id === id)?.nombre ?? "el otro operador";
  const opcionesSelect = operadores.map((o) => ({
    id: o.id,
    label: o.nombre,
    sublabel: o.sublabel,
    color: o.color,
  }));
  const opcionesFranjas = alcanceOptions.map((o) => ({ id: o.id, label: o.label }));

  const handleSubmit = () => {
    if (!completo || !operadorAId || !operadorBId) return;
    setSaving(true);
    onError(null);
    const payload: IntercambioPayload = {
      operadorAId,
      operadorBId,
      desde,
      hasta,
      alcanceItemsA: alcance === "total" ? null : franjasA,
      alcanceItemsB: alcance === "total" ? null : franjasB,
      motivo: motivo.trim() || null,
    };
    (intercambio ? api.update(intercambio.id, payload) : api.create(payload))
      .then(onSaved)
      .catch((err: unknown) => {
        console.error("Error al guardar el intercambio:", err);
        onError(err instanceof ApiError ? err.message : "No se pudo guardar el intercambio.");
      })
      .finally(() => setSaving(false));
  };

  return (
    <div className="flex flex-col gap-4">
      <SearchableSelect
        label="Operador A"
        options={opcionesSelect}
        value={operadorAId}
        onChange={setOperadorAId}
        exclude={operadorBId ? [operadorBId] : undefined}
        placeholder="Buscá operador…"
      />
      <SearchableSelect
        label="Operador B"
        options={opcionesSelect}
        value={operadorBId}
        onChange={setOperadorBId}
        exclude={operadorAId ? [operadorAId] : undefined}
        placeholder="Buscá operador…"
      />

      <div className="grid grid-cols-2 gap-3">
        <BrandInput
          label="Desde"
          type="date"
          value={desde}
          min={intercambio ? undefined : hoyIso()}
          onChange={(e) => {
            setDesde(e.target.value);
            // Un cambio de turno suele ser de un solo día: se precarga Hasta.
            if (!hasta || hasta < e.target.value) setHasta(e.target.value);
          }}
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
            { value: "parcial", label: "Franjas específicas" },
          ]}
          value={alcance}
          onChange={(v) => setAlcance(v as "total" | "parcial")}
        />
        {alcance === "total" && (
          <p className="font-body text-xs text-muted-foreground">
            Se intercambian todas las franjas de ambos operadores.
          </p>
        )}
      </div>

      {alcance === "parcial" && (
        <>
          <SearchableSelect
            label={`Franjas de ${nombreDe(operadorAId)} que toma ${nombreDe(operadorBId)}`}
            options={opcionesFranjas}
            multiple
            value={franjasA}
            onChange={setFranjasA}
            placeholder="Buscá una franja…"
            error={franjasA.length === 0 ? "Seleccioná al menos una franja." : undefined}
          />
          <SearchableSelect
            label={`Franjas de ${nombreDe(operadorBId)} que toma ${nombreDe(operadorAId)}`}
            options={opcionesFranjas}
            multiple
            value={franjasB}
            onChange={setFranjasB}
            placeholder="Buscá una franja…"
            error={franjasB.length === 0 ? "Seleccioná al menos una franja." : undefined}
          />
        </>
      )}

      <BrandInput
        label="Motivo"
        value={motivo}
        placeholder="Intercambio"
        onChange={(e) => setMotivo(e.target.value)}
      />

      <p className="rounded-[8px] bg-muted/30 px-4 py-3 font-body text-xs leading-relaxed text-muted-foreground">
        El intercambio es temporal y no modifica la Configuración de Turnos. Al finalizar el{" "}
        {hasta ? formatFechaCorta(hasta) : "…"}, cada operador vuelve a sus franjas
        automáticamente. Se registra como dos coberturas cruzadas que se editan y cancelan juntas.
      </p>

      <div className="flex justify-end gap-2 pt-1">
        <BrandButton variant="outline" onClick={onClose}>
          Cancelar
        </BrandButton>
        <BrandButton onClick={handleSubmit} disabled={!completo} loading={saving}>
          {saving ? "Guardando…" : intercambio ? "Guardar cambios" : "Guardar intercambio"}
        </BrandButton>
      </div>
    </div>
  );
}
