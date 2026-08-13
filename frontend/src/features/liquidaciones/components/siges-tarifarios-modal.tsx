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

function ZonaMapRow({ zona, onMapeada }: { zona: ZonaSigesEstado; onMapeada: () => void }) {
  const [seleccion, setSeleccion] = useState(zona.propuesta ?? ZONA_GENERICA);
  const [saving, setSaving] = useState(false);

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
          <option value={USAR_NOMBRE_SIGES}>Usar el nombre de Siges tal cual</option>
          {zona.zonasLocales.map((z) => (
            <option key={z} value={z}>
              {z}
              {zona.propuesta === z ? " (propuesta)" : ""}
            </option>
          ))}
        </BrandSelect>
      </div>
      <BrandButton size="sm" variant="outline" loading={saving} onClick={handleMapear}>
        Mapear
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
              {c.valorLocal} vs Siges {c.valorSiges}
            </p>
          ))}
        </>
      )}
      <p className="font-body text-xs text-muted-foreground mt-2">
        Sin cambios: {resultado.sinCambios}
        {resultado.prestadoresSinVinculo.length > 0 &&
          ` · Sin vínculo Siges: ${resultado.prestadoresSinVinculo.join(", ")}`}
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
          setError(err instanceof Error ? err.message : "Error al consultar Siges");
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
    <BrandModal isOpen onClose={onClose} title="Sincronizar tarifarios con Siges" error={error}>
      {zonas === null || resultado === null ? (
        <div className="flex h-32 items-center justify-center">{!error && <Spinner />}</div>
      ) : (
        <div className="flex max-h-[65vh] flex-col gap-5 overflow-y-auto pr-1">
          {sinMapear.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>
                Zonas de Siges sin mapear ({sinMapear.length}) — sus tarifas no se sincronizan
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
              <p className={`${seccionCls} mb-1`}>Zonas mapeadas</p>
              {mapeadas.map((z) => (
                <p
                  key={`${z.prestadorId}-${z.descripcionSiges}`}
                  className="font-body text-xs text-muted-foreground"
                >
                  {z.prestador} · {z.descripcionSiges} → {z.zonaLocal ?? "Genérica (sin zona)"}
                </p>
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
