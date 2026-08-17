"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { AuditarPinesResult, PinSospechoso } from "../types/liquidaciones";

function PinSospechosoItem({ pin, prestadorId, onCorregido }: {
  pin: PinSospechoso; prestadorId: string; onCorregido: () => void;
}) {
  const [corrigiendo, setCorrigiendo] = useState(false);
  const corregir = async () => {
    setCorrigiendo(true);
    try {
      await liquidacionesApi.corregirPin(prestadorId, pin.sigesSucursalId);
      toast.success(`${pin.empresaNombre}: pin corregido con geocode`);
      onCorregido();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al corregir pin");
    } finally { setCorrigiendo(false); }
  };
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">{pin.empresaNombre} — {pin.sucursalNombre}</p>
        <Badge variant={pin.locationType === "ROOFTOP" ? "danger" : "warning"}>{pin.discrepanciaKm.toFixed(1)} km · {pin.locationType}</Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">{pin.direccion}</p>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="flex gap-3 font-body text-[11px] font-bold uppercase tracking-wide">
          <a href={`https://www.google.com/maps?q=${pin.latitudSiges},${pin.longitudSiges}`} target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">Pin Siges</a>
          <a href={`https://www.google.com/maps?q=${pin.latitudGeocode},${pin.longitudGeocode}`} target="_blank" rel="noopener noreferrer" className="text-brand-orange hover:underline">Geocode</a>
        </div>
        <BrandButton type="button" size="sm" variant="outline" loading={corrigiendo} onClick={corregir}>
          Corregir pin
        </BrandButton>
      </div>
    </div>
  );
}

export function PasoPines({ prestadorId }: { prestadorId: string }) {
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
      const r = await liquidacionesApi.auditarPines(prestadorId);
      setResultado(r);
      setKey(k => k + 1);
    } finally { setAuditando(false); }
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Compara el pin de Siges de cada sucursal contra el geocode de su domicilio (umbral: 5 km).
        Si el pin difiere demasiado, podés reemplazarlo con el geocode — eso mejora la precisión
        del cálculo de distancias. Este paso es opcional.
      </p>
      {!pines ? (
        <div className="flex h-20 items-center justify-center"><Spinner /></div>
      ) : pines.length > 0 ? (
        <div className="flex max-h-[35vh] flex-col gap-2 overflow-y-auto pr-1">
          {pines.map((p) => (
            <PinSospechosoItem
              key={p.sigesSucursalId}
              pin={p}
              prestadorId={prestadorId}
              onCorregido={() => setKey(k => k + 1)}
            />
          ))}
        </div>
      ) : resultado ? (
        <p className="font-body text-sm text-muted-foreground italic">
          ✓ Sin discrepancias mayores a 5 km
          {resultado.geocodificadas > 0 && ` (${resultado.geocodificadas} geocodificadas, ${resultado.llamadasGoogle} llamadas Google)`}.
          Podés finalizar.
        </p>
      ) : (
        <p className="font-body text-sm text-muted-foreground italic">
          Hacé clic en &quot;Verificar pines con Google&quot; para comparar los pines de Siges
          contra el domicilio de cada sucursal. No modifica nada — solo detecta cuáles
          difieren más de 5 km para que puedas corregirlos.
        </p>
      )}
      <BrandButton variant="outline" size="sm" loading={auditando} onClick={auditar}>
        Verificar pines con Google
      </BrandButton>
    </div>
  );
}
