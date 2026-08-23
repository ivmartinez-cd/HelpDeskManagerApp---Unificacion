"use client";

import { useState } from "react";
import { ApiError } from "@/services/http-client";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { preventivosApi } from "../api/preventivos-api";
import type { PuntoMapaPreventivo } from "../types/preventivos";

// Mismo bbox de Argentina que domain/services/coordenadas.py (backend, fuente
// de verdad) — acá es solo feedback rápido, no reemplaza esa validación.
const LAT_MIN = -55.5;
const LAT_MAX = -21.5;
const LON_MIN = -73.6;
const LON_MAX = -53.0;

interface CorregirCoordenadaModalProps {
  punto: PuntoMapaPreventivo;
  onClose: () => void;
  onSaved: () => void;
}

function coordenadaValida(valor: number, min: number, max: number): boolean {
  return Number.isFinite(valor) && valor >= min && valor <= max;
}

/** Corrección manual de una sucursal mal ubicada, disparada desde el botón
 * "Corregir ubicación" del popup del mapa (2026-08-23) — la única vía hasta
 * ahora era editar `preventivos_sucursal_coordenadas` a mano en la DB. */
export function CorregirCoordenadaModal({ punto, onClose, onSaved }: CorregirCoordenadaModalProps) {
  const [latitud, setLatitud] = useState(String(punto.latitud ?? ""));
  const [longitud, setLongitud] = useState(String(punto.longitud ?? ""));
  const [nota, setNota] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const latNum = Number(latitud);
  const lonNum = Number(longitud);
  const completo =
    latitud.trim() !== "" &&
    longitud.trim() !== "" &&
    coordenadaValida(latNum, LAT_MIN, LAT_MAX) &&
    coordenadaValida(lonNum, LON_MIN, LON_MAX);

  const handleSubmit = () => {
    if (!completo) return;
    setSaving(true);
    setSaveError(null);
    preventivosApi
      .corregirCoordenada(punto.id_sucursal, latNum, lonNum, nota)
      .then(onSaved)
      .catch((err: unknown) => {
        setSaveError(err instanceof ApiError ? err.message : "No se pudo guardar la corrección.");
      })
      .finally(() => setSaving(false));
  };

  return (
    <BrandModal isOpen title="Corregir ubicación" onClose={onClose} widthPx={420} error={saveError}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-0.5">
          <p className="font-body text-sm font-semibold text-foreground">{punto.cliente}</p>
          <p className="font-body text-xs text-muted-foreground">
            {punto.sucursal} · {punto.zona}
          </p>
          {punto.domicilio && (
            <p className="font-body text-xs text-muted-foreground">{punto.domicilio}</p>
          )}
        </div>

        <BrandInput
          label="Latitud"
          type="number"
          step="any"
          value={latitud}
          onChange={(e) => setLatitud(e.target.value)}
        />
        <BrandInput
          label="Longitud"
          type="number"
          step="any"
          value={longitud}
          onChange={(e) => setLongitud(e.target.value)}
        />
        <BrandInput
          label="Nota (opcional)"
          hint="Por qué se corrigió — queda como auditoría."
          value={nota}
          onChange={(e) => setNota(e.target.value)}
          maxLength={300}
        />

        <div className="flex justify-end gap-2 pt-2">
          <BrandButton variant="outline" onClick={onClose} disabled={saving}>
            Cancelar
          </BrandButton>
          <BrandButton onClick={handleSubmit} disabled={!completo} loading={saving}>
            Guardar
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
