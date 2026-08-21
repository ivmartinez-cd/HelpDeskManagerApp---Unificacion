"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  SyncTarifariosResult,
  ZonaSigesEstado,
  ZonasSiges,
} from "../types/liquidaciones";

const seccionCls = "font-heading text-xs font-bold uppercase tracking-[.06em] text-muted-foreground";
const filaCls = "flex items-end justify-between gap-3 border-t border-border py-2 first:border-t-0";

// Sentinels del select: zona genérica (tarifario sin zona — el caso mayoritario,
// códigos TMT*) y "adoptar el nombre de Siges como zona local nueva".
const ZONA_GENERICA = "__generica__";
const USAR_NOMBRE_SIGES = "__siges__";

// Selección inicial del select: si ya está mapeada, reflejar el mapeo actual
// (no la propuesta) para que remapear parta de dónde está hoy, no de cero.
function seleccionInicialDe(zona: ZonaSigesEstado): string {
  if (!zona.mapeada) return zona.propuesta ?? ZONA_GENERICA;
  if (zona.zonaLocal === null) return ZONA_GENERICA;
  if (zona.zonaLocal === zona.descripcionSiges) return USAR_NOMBRE_SIGES;
  return zona.zonaLocal;
}

function ZonaMapRow({ zona, onMapeada }: { zona: ZonaSigesEstado; onMapeada: () => void }) {
  const [seleccion, setSeleccion] = useState(() => seleccionInicialDe(zona));
  const [saving, setSaving] = useState(false);

  // El mapeo vigente puede ser una zona que ya no aparece en `zonasLocales`
  // (ninguna tarifa la usa todavía) — agregarla para no perderla del select.
  const opciones =
    zona.zonaLocal && zona.zonaLocal !== zona.descripcionSiges && !zona.zonasLocales.includes(zona.zonaLocal)
      ? [...zona.zonasLocales, zona.zonaLocal].sort()
      : zona.zonasLocales;

  const handleMapear = async () => {
    setSaving(true);
    try {
      await liquidacionesApi.mapearZonaSiges({
        prestadorId: zona.prestadorId,
        descripcionSiges: zona.descripcionSiges,
        zonaLocal:
          seleccion === ZONA_GENERICA
            ? null
            : seleccion === USAR_NOMBRE_SIGES
              ? zona.descripcionSiges
              : seleccion,
      });
      toast.success("Zona mapeada");
      onMapeada();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al mapear");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={filaCls}>
      <div className="min-w-0 flex-1">
        <p className="truncate font-body text-sm text-foreground">
          <span className="font-bold">{zona.prestador}</span> · {zona.descripcionSiges}
        </p>
        <BrandSelect
          label="Zona local"
          value={seleccion}
          onChange={(e) => setSeleccion(e.target.value)}
        >
          <option value={ZONA_GENERICA}>Zona genérica (tarifario sin zona)</option>
          <option value={USAR_NOMBRE_SIGES}>Usar el nombre tal cual</option>
          {opciones.map((z) => (
            <option key={z} value={z}>
              {z}
              {zona.propuesta === z ? " (propuesta)" : ""}
            </option>
          ))}
        </BrandSelect>
      </div>
      <BrandButton size="sm" variant="outline" loading={saving} onClick={handleMapear}>
        {zona.mapeada ? "Remapear" : "Mapear"}
      </BrandButton>
    </div>
  );
}

function ResultadoSyncTarifarios({ resultado }: { resultado: SyncTarifariosResult }) {
  return (
    <div className="flex flex-col gap-2">
      <p className={seccionCls}>
        {resultado.dryRun
          ? `A crear: ${resultado.creados} vigencia(s) (simulación)`
          : `Creadas: ${resultado.creados} vigencia(s)`}
      </p>
      {resultado.gruposCreados.map((g) => (
        <p
          key={`${g.prestador}-${g.tipoServicio}-${g.zona ?? ""}`}
          className="font-body text-sm text-foreground"
        >
          <span className="font-bold">{g.prestador}</span> · {g.tipoServicio}
          {g.zona ? ` · ${g.zona}` : ""} → {g.cantidad} vigencia(s)
        </p>
      ))}
      {resultado.conflictos.length > 0 && (
        <>
          <p className={`${seccionCls} mt-2 text-destructive`}>
            Conflictos (no se pisan — resolver a mano)
          </p>
          {resultado.conflictos.map((c, i) => (
            <p key={i} className="font-body text-xs text-muted-foreground">
              {c.prestador} · {c.tipoServicio}
              {c.zona ? ` · ${c.zona}` : ""} · desde {c.vigenciaDesde}: {c.campo} local{" "}
              {c.valorLocal} vs {c.valorSiges}
            </p>
          ))}
        </>
      )}
      <p className="font-body text-xs text-muted-foreground mt-2">
        Sin cambios: {resultado.sinCambios}
        {resultado.prestadoresSinVinculo.length > 0 &&
          ` · Sin vínculo: ${resultado.prestadoresSinVinculo.join(", ")}`}
      </p>
    </div>
  );
}

export function SigesTarifariosModal({
  onClose,
  onChanged,
}: {
  onClose: () => void;
  onChanged: () => void;
}) {
  const [zonas, setZonas] = useState<ZonasSiges | null>(null);
  const [resultado, setResultado] = useState<SyncTarifariosResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Promise-chain: ver nota en siges-sync-modal.tsx (regla set-state-in-effect).
  const load = useCallback(
    () =>
      Promise.all([liquidacionesApi.getSigesZonas(), liquidacionesApi.syncTarifariosSiges(true)])
        .then(([z, dry]) => {
          setZonas(z);
          setResultado(dry);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al consultar");
        }),
    [],
  );

  useEffect(() => { void load(); }, [load]);

  const handleAplicar = async () => {
    setSyncing(true);
    try {
      const res = await liquidacionesApi.syncTarifariosSiges(false);
      setResultado(res);
      toast.success(`Sync aplicado: ${res.creados} vigencia(s) nueva(s)`);
      onChanged();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al sincronizar");
    } finally {
      setSyncing(false);
    }
  };

  const sinMapear = zonas?.zonas.filter((z) => !z.mapeada) ?? [];
  const mapeadas = zonas?.zonas.filter((z) => z.mapeada) ?? [];

  return (
    <BrandModal isOpen onClose={onClose} title="Sincronizar tarifarios" error={error}>
      {zonas === null || resultado === null ? (
        <div className="flex h-32 items-center justify-center">{!error && <Spinner />}</div>
      ) : (
        <div className="flex max-h-[65vh] flex-col gap-5 overflow-y-auto pr-1">
          {sinMapear.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>
                Zonas sin mapear ({sinMapear.length}) — sus tarifas no se sincronizan
                hasta confirmar el mapeo
              </p>
              {sinMapear.map((z) => (
                <ZonaMapRow
                  key={`${z.prestadorId}-${z.descripcionSiges}`}
                  zona={z}
                  onMapeada={load}
                />
              ))}
            </div>
          )}

          {mapeadas.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>
                Zonas mapeadas ({mapeadas.length}) — se puede remapear
              </p>
              {mapeadas.map((z) => (
                <ZonaMapRow
                  key={`${z.prestadorId}-${z.descripcionSiges}`}
                  zona={z}
                  onMapeada={load}
                />
              ))}
            </div>
          )}

          <ResultadoSyncTarifarios resultado={resultado} />

          <div className="flex justify-end gap-3 pt-1">
            <BrandButton variant="outline" onClick={onClose}>Cerrar</BrandButton>
            <BrandButton
              loading={syncing}
              disabled={resultado.creados === 0 || !resultado.dryRun}
              onClick={handleAplicar}
            >
              Aplicar sync
            </BrandButton>
          </div>
        </div>
      )}
    </BrandModal>
  );
}
