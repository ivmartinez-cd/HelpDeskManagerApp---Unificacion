"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  Spst,
  SyncTarifariosResult,
  ZonaSigesEstado,
  ZonasSiges,
} from "../types/liquidaciones";

const seccionCls = "font-heading text-xs font-bold uppercase tracking-[.06em] text-muted-foreground";
const filaCls = "flex items-end justify-between gap-3 border-t border-border py-2 first:border-t-0";

// Sentinel del select: tarifa genérica (tarifario sin SPST — el caso
// mayoritario, códigos TMT*).
const GENERICA = "__generica__";

// Selección inicial del select: si ya está mapeada, reflejar el mapeo actual
// (no la propuesta) para que remapear parta de dónde está hoy, no de cero.
function seleccionInicialDe(zona: ZonaSigesEstado): string {
  if (!zona.mapeada) return zona.propuestaSpstId ?? GENERICA;
  return zona.spstId ?? GENERICA;
}

function ZonaMapRow({
  zona, spsts, onMapeada,
}: {
  zona: ZonaSigesEstado;
  spsts: Spst[];
  onMapeada: () => void;
}) {
  const [seleccion, setSeleccion] = useState(() => seleccionInicialDe(zona));
  const [saving, setSaving] = useState(false);

  const handleMapear = async () => {
    setSaving(true);
    try {
      await liquidacionesApi.mapearZonaSiges({
        prestadorId: zona.prestadorId,
        descripcionSiges: zona.descripcionSiges,
        spstId: seleccion === GENERICA ? null : seleccion,
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
        <p className="truncate font-body text-sm text-foreground">{zona.descripcionSiges}</p>
        <BrandSelect
          label="SPST"
          value={seleccion}
          onChange={(e) => setSeleccion(e.target.value)}
        >
          <option value={GENERICA}>Genérica (tarifario sin SPST)</option>
          {spsts.map((s) => (
            <option key={s.id} value={s.id}>
              {s.nombre}
              {zona.propuestaSpstId === s.id ? " (propuesta)" : ""}
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
          key={`${g.tipoServicio}-${g.spstNombre ?? ""}`}
          className="font-body text-sm text-foreground"
        >
          {g.tipoServicio} · {g.spstNombre ?? "Genérica"} → {g.cantidad} vigencia(s)
        </p>
      ))}
      {resultado.conflictos.length > 0 && (
        <>
          <p className={`${seccionCls} mt-2 text-destructive`}>
            Conflictos (no se pisan — resolver a mano)
          </p>
          {resultado.conflictos.map((c, i) => (
            <p key={i} className="font-body text-xs text-muted-foreground">
              {c.tipoServicio} · {c.spstNombre ?? "Genérica"} · desde {c.vigenciaDesde}:{" "}
              {c.campo} local {c.valorLocal} vs {c.valorSiges}
            </p>
          ))}
        </>
      )}
      {resultado.prestadoresSinGenerica.length > 0 && (
        <p className="font-body text-xs text-destructive mt-2">
          {resultado.prestadoresSinGenerica.join(", ")} no tiene ninguna tarifa Genérica:
          las sucursales sin SPST en Tabla KM van a quedar sin precio (ALT008 en cada
          incidente). Mapeá la zona de la sede del prestador a &quot;Genérica&quot;.
        </p>
      )}
      {resultado.prestadoresSinVinculo.length > 0 && (
        <p className="font-body text-xs text-destructive mt-2">
          {resultado.prestadoresSinVinculo[0]} no está vinculado a Siges — vinculalo en
          Configuración &gt; Prestadores antes de sincronizar.
        </p>
      )}
      <p className="font-body text-xs text-muted-foreground mt-2">
        Sin cambios: {resultado.sinCambios}
      </p>
    </div>
  );
}

export function SigesTarifariosModal({
  prestadorId,
  prestadorNombre,
  onClose,
  onChanged,
}: {
  prestadorId: string;
  prestadorNombre: string;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [zonas, setZonas] = useState<ZonasSiges | null>(null);
  const [spsts, setSpsts] = useState<Spst[]>([]);
  const [resultado, setResultado] = useState<SyncTarifariosResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Promise-chain: ver nota en siges-sync-modal.tsx (regla set-state-in-effect).
  const load = useCallback(
    () =>
      Promise.all([
        liquidacionesApi.getSigesZonas(prestadorId),
        liquidacionesApi.syncTarifariosSiges(true, prestadorId),
        liquidacionesApi.listSpsts({ prestadorId }),
      ])
        .then(([z, dry, s]) => {
          setZonas(z);
          setResultado(dry);
          setSpsts(s);
          setError(null);
        })
        .catch((err: unknown) => {
          setError(err instanceof Error ? err.message : "Error al consultar");
        }),
    [prestadorId],
  );

  useEffect(() => { void load(); }, [load]);

  const handleAplicar = async () => {
    setSyncing(true);
    try {
      const res = await liquidacionesApi.syncTarifariosSiges(false, prestadorId);
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
    <BrandModal isOpen onClose={onClose} title={`Sincronizar tarifarios · ${prestadorNombre}`} error={error}>
      {zonas === null || resultado === null ? (
        <div className="flex h-32 items-center justify-center">{!error && <Spinner />}</div>
      ) : (
        <div className="flex max-h-[65vh] flex-col gap-5 overflow-y-auto pr-1">
          {sinMapear.length > 0 && (
            <div>
              <p className={`${seccionCls} mb-1`}>
                Zonas sin mapear ({sinMapear.length}) — sus tarifas no se sincronizan
                hasta confirmar el mapeo. &quot;Mapear&quot; guarda al toque, aunque después
                cierres sin tocar &quot;Aplicar sync&quot;
              </p>
              {sinMapear.map((z) => (
                <ZonaMapRow
                  key={`${z.prestadorId}-${z.descripcionSiges}`}
                  zona={z}
                  spsts={spsts}
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
                  spsts={spsts}
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
