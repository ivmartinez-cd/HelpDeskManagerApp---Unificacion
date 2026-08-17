"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  AuditarPinesResult, EstadoAsistenteKm, PinSospechoso,
} from "../types/liquidaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";

function PinSospechosoItem({ pin, prestadorId, onCorregido }: {
  pin: PinSospechoso; prestadorId: string; onCorregido: () => void;
}) {
  const [corrigiendo, setCorrigiendo] = useState(false);
  const corregir = async () => {
    setCorrigiendo(true);
    try {
      await liquidacionesApi.corregirPin(prestadorId, pin.sigesSucursalId);
      toast.success(`${pin.empresaNombre}: pin corregido`);
      onCorregido();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al corregir pin");
    } finally { setCorrigiendo(false); }
  };
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">{pin.empresaNombre} — {pin.sucursalNombre}</p>
        <Badge variant={pin.locationType === "ROOFTOP" ? "danger" : "warning"}>
          {pin.discrepanciaKm.toFixed(1)} km de diferencia
        </Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">{pin.direccion}</p>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="flex gap-3 font-body text-[11px] font-bold uppercase tracking-wide">
          <a href={`https://www.google.com/maps?q=${pin.latitudSiges},${pin.longitudSiges}`} target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">Ver pin de Gestión</a>
          <a href={`https://www.google.com/maps?q=${pin.latitudGeocode},${pin.longitudGeocode}`} target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">Ver dirección escrita</a>
        </div>
        <BrandButton type="button" size="sm" variant="outline" loading={corrigiendo} onClick={corregir}>
          Usar la dirección escrita
        </BrandButton>
      </div>
    </div>
  );
}

/** Paso Pines. El listado es cache-first (sin Google); la verificación con
 * Google solo corre tras confirmar el costo. Corregir no consulta nada. */
export function PasoPines({ prestadorId, estado, onCambio }: {
  prestadorId: string; estado: EstadoAsistenteKm; onCambio: () => void;
}) {
  const [pines, setPines] = useState<PinSospechoso[] | null>(null);
  const [auditando, setAuditando] = useState(false);
  const [resultado, setResultado] = useState<AuditarPinesResult | null>(null);
  const [key, setKey] = useState(0);

  useEffect(() => {
    liquidacionesApi.listPinesSospechosos(prestadorId).then(setPines).catch(() => setPines([]));
  }, [prestadorId, key]);

  const auditar = async () => {
    setAuditando(true);
    try {
      setResultado(await liquidacionesApi.auditarPines(prestadorId));
      setKey(k => k + 1);
      onCambio();
    } finally { setAuditando(false); }
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Acá comparamos el pin del mapa de Gestión contra la dirección escrita de cada
        sucursal. Si difieren en más de 5 km, el pin probablemente esté mal puesto y
        conviene usar la dirección escrita — mejora el cálculo de km. Este paso es
        opcional y corregir no consulta Google.
      </p>
      {!pines ? (
        <div className="flex h-20 items-center justify-center"><Spinner /></div>
      ) : pines.length > 0 ? (
        <div className="flex max-h-[32vh] flex-col gap-2 overflow-y-auto pr-1">
          {pines.map((p) => (
            <PinSospechosoItem
              key={p.sigesSucursalId}
              pin={p}
              prestadorId={prestadorId}
              onCorregido={() => { setKey(k => k + 1); onCambio(); }}
            />
          ))}
        </div>
      ) : resultado ? (
        <p className="font-body text-sm text-muted-foreground italic">
          ✓ Ningún pin difiere más de 5 km de su dirección. Podés finalizar.
        </p>
      ) : (
        <p className="font-body text-sm text-muted-foreground italic">
          Todavía no hay pines dudosos detectados. &quot;Verificar pines&quot; compara
          cada pin contra su dirección — no modifica nada, solo detecta.
        </p>
      )}
      <BotonConsumoGoogle
        variant="outline"
        size="sm"
        estimacion={estado.estimacionAuditarPines}
        tope={estado.topePorCorrida}
        loading={auditando}
        onEjecutar={auditar}
      >
        Verificar pines
      </BotonConsumoGoogle>
    </div>
  );
}
