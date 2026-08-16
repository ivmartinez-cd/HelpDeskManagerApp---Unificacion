"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { CalculoKmPreview, PrestadorLiquidacion } from "../types/liquidaciones";

const LABEL_COORDS_ORIGEN: Record<string, string> = {
  siges: "Siges",
  geocode: "Geocodificado",
  manual: "Manual",
};
const th = "py-2 px-3 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const td = "py-1.5 px-3 font-body text-[13px]";

export function PasoCalcular({ prestador, preview, setPreview, onAplicado }: {
  prestador: PrestadorLiquidacion; preview: CalculoKmPreview | null;
  setPreview: (p: CalculoKmPreview) => void; onAplicado: () => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [aplicando, setAplicando] = useState(false);
  const [aplicado, setAplicado] = useState(false);
  const fetched = useRef(false);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (fetched.current || preview) return;
    fetched.current = true;
    liquidacionesApi.previewCalcularDistancias(prestador.id).then(setPreview)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al generar preview"));
  }, []);

  if (!preview && !error) return (
    <div className="flex h-40 flex-col items-center justify-center gap-3">
      <Spinner /><p className="font-body text-sm text-muted-foreground">Consultando Google Maps (ida y vuelta por sucursal)…</p>
    </div>
  );
  if (error) {
    const sinBase = error.includes("sucursal base");
    return (
      <div className="rounded-[8px] border border-destructive/40 bg-destructive/5 p-4 flex flex-col gap-2">
        <p className="font-body text-sm font-semibold text-destructive">
          {sinBase ? "Falta configurar la sucursal base de despacho" : "Error al calcular distancias"}
        </p>
        {sinBase ? (
          <p className="font-body text-sm text-muted-foreground">
            Para calcular distancias necesitás definir desde qué sucursal propia sale el técnico.
            Configurala en <span className="font-semibold text-foreground">Configuración → Prestadores → {prestador.nombre}</span>, campo <span className="font-semibold text-foreground">Sucursal base</span>.
          </p>
        ) : (
          <p className="font-body text-sm text-muted-foreground">{error}</p>
        )}
      </div>
    );
  }
  if (aplicado) return <p className="font-body text-sm font-semibold text-brand-orange">✓ Distancias aplicadas. Podés continuar al paso de auditoría.</p>;

  const aplicar = async () => {
    if (!preview) return;
    setAplicando(true);
    try {
      const res = await liquidacionesApi.aplicarCalcularDistancias(prestador.id, preview.id);
      toast.success(`Aplicado: ${res.creadas} creadas, ${res.actualizadas} actualizadas`);
      onAplicado(); setAplicado(true);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error al aplicar"); }
    finally { setAplicando(false); }
  };

  return preview ? (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        <Badge variant="info">{preview.filas.filter(f => f.accion === "crear").length} a crear</Badge>
        <Badge variant="accent">{preview.filas.filter(f => f.accion === "actualizar").length} a actualizar</Badge>
        <Badge variant="neutral">{preview.sinUbicar} sin ubicar</Badge>
        {preview.sinRuta > 0 && <Badge variant="warning">{preview.sinRuta} sin ruta</Badge>}
        <Badge variant="neutral">{preview.elementosGoogle} llamadas Google</Badge>
      </div>
      <div className="max-h-[35vh] overflow-y-auto rounded-[8px] border border-border">
        <table className="w-full">
          <thead className="sticky top-0 bg-card"><tr className="bg-muted/40">
            <th className={th}>Empresa</th><th className={th}>Sucursal</th>
            <th className={`${th} text-right`}>Actual</th><th className={`${th} text-right`}>Ida</th>
            <th className={`${th} text-right`}>Vuelta</th><th className={`${th} text-right`}>Total</th>
            <th className={th}>Coords</th><th className={th}>Acción</th>
          </tr></thead>
          <tbody>
            {preview.filas.map((f) => (
              <tr key={`${f.empresaNombre}::${f.sucursalNombre}`} className="border-t border-border">
                <td className={td}><span className="block max-w-[130px] truncate text-foreground" title={f.empresaNombre}>{f.empresaNombre}</span></td>
                <td className={td}><span className="block max-w-[160px] truncate text-foreground" title={f.sucursalNombre}>{f.sucursalNombre}</span></td>
                <td className={`${td} text-right tabular-nums text-muted-foreground`}>{f.kmsRecorridoActual != null ? f.kmsRecorridoActual.toFixed(1) : "—"}</td>
                <td className={`${td} text-right tabular-nums text-foreground`}>{f.kmsIda.toFixed(1)}</td>
                <td className={`${td} text-right tabular-nums text-foreground`}>{f.kmsVuelta.toFixed(1)}</td>
                <td className={`${td} text-right tabular-nums font-semibold text-foreground`}>{f.kmsTotal.toFixed(1)}</td>
                <td className={td}><Badge variant={f.coordsOrigen === "siges" ? "neutral" : "info"}>{LABEL_COORDS_ORIGEN[f.coordsOrigen] ?? f.coordsOrigen}</Badge></td>
                <td className={td}><Badge variant={f.accion === "crear" ? "info" : "accent"}>{f.accion}</Badge></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <BrandButton loading={aplicando} onClick={aplicar} className="self-start">Aplicar {preview.filas.length} cambios</BrandButton>
    </div>
  ) : null;
}
