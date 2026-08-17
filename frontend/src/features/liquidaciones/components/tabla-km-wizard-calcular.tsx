"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  CalculoKmPreview, EstadoAsistenteKm, PrestadorLiquidacion,
} from "../types/liquidaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";

const LABEL_COORDS_ORIGEN: Record<string, string> = {
  siges: "Siges",
  geocode: "Geocodificado",
  manual: "Manual",
};
const th = "py-2 px-3 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const td = "py-1.5 px-3 font-body text-[13px]";

/** Paso Distancias. NUNCA consulta Google al entrar: muestra el resumen del
 * diagnóstico y recién calcula cuando la TL confirma el costo. */
export function PasoCalcular({ prestador, estado, preview, setPreview, onCambio, irAUbicar }: {
  prestador: PrestadorLiquidacion;
  estado: EstadoAsistenteKm;
  preview: CalculoKmPreview | null;
  setPreview: (p: CalculoKmPreview | null) => void;
  onCambio: () => void;
  irAUbicar: () => void;
}) {
  const [calculando, setCalculando] = useState(false);
  const [aplicando, setAplicando] = useState(false);
  const [aplicado, setAplicado] = useState(false);
  const [confirmarAplicar, setConfirmarAplicar] = useState(false);
  const [calcularIgual, setCalcularIgual] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calcular = async () => {
    setCalculando(true); setError(null);
    try {
      setPreview(await liquidacionesApi.previewCalcularDistancias(prestador.id));
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al calcular distancias");
    } finally { setCalculando(false); }
  };

  const aplicar = async () => {
    if (!preview) return;
    setConfirmarAplicar(false);
    setAplicando(true);
    try {
      const res = await liquidacionesApi.aplicarCalcularDistancias(prestador.id, preview.id);
      toast.success(`Listo: ${res.creadas} filas creadas, ${res.actualizadas} actualizadas`);
      setAplicado(true);
      setPreview(null);
      onCambio();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al aplicar");
    } finally { setAplicando(false); }
  };

  if (aplicado) {
    return (
      <p className="font-body text-sm font-semibold text-brand-orange">
        ✓ Distancias aplicadas a tu Tabla KM. Podés continuar al paso de pines.
      </p>
    );
  }

  const aCrear = preview?.filas.filter(f => f.accion === "crear").length ?? 0;
  const aActualizar = preview?.filas.filter(f => f.accion === "actualizar").length ?? 0;
  const gateSinUbicar = estado.sinCoordenadas > 0 && !calcularIgual && !preview;

  return (
    <div className="flex flex-col gap-4">
      {!preview && (
        <p className="font-body text-sm text-muted-foreground">
          Se van a calcular los km de ida y vuelta (con Google Maps) para{" "}
          <span className="font-semibold text-foreground">
            {estado.estimacionDistancias / 2} sucursales con ubicación
          </span>. Primero ves el resultado; nada se guarda hasta que apliques.
        </p>
      )}

      {gateSinUbicar && (
        <div className="rounded-[8px] border border-warning/40 bg-warning/5 p-4 flex flex-col gap-3">
          <p className="font-body text-sm font-semibold text-foreground">
            Hay {estado.sinCoordenadas} sucursales sin ubicación en el mapa
          </p>
          <p className="font-body text-sm text-muted-foreground">
            Si calculás ahora, esas {estado.sinCoordenadas} van a quedar <strong>sin km</strong>.
            Lo recomendado es ubicarlas primero en el paso anterior.
          </p>
          <div className="flex flex-wrap gap-2">
            <BrandButton size="sm" onClick={irAUbicar}>Ir a Ubicar primero (recomendado)</BrandButton>
            <BrandButton size="sm" variant="outline" onClick={() => setCalcularIgual(true)}>
              Calcular igual — las {estado.sinCoordenadas} quedan sin km
            </BrandButton>
          </div>
        </div>
      )}

      {!preview && !gateSinUbicar && (
        <BotonConsumoGoogle
          estimacion={estado.estimacionDistancias}
          tope={estado.topePorCorrida}
          bloquearSobreTope
          loading={calculando}
          onEjecutar={calcular}
        >
          Calcular distancias
        </BotonConsumoGoogle>
      )}

      {error && <p className="font-body text-sm text-destructive">{error}</p>}

      {preview && (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <Badge variant="info">{aCrear} filas nuevas</Badge>
            <Badge variant="accent">{aActualizar} filas a actualizar</Badge>
            <Badge variant="neutral">{preview.sinUbicar} sin ubicar</Badge>
            {preview.sinRuta > 0 && <Badge variant="warning">{preview.sinRuta} sin ruta</Badge>}
            {preview.sinActividad > 0 && <Badge variant="neutral">{preview.sinActividad} ex-clientes omitidos</Badge>}
            <Badge variant="neutral">{preview.elementosGoogle} consultas usadas</Badge>
          </div>
          <div className="max-h-[32vh] overflow-y-auto rounded-[8px] border border-border">
            <table className="w-full">
              <thead className="sticky top-0 bg-card"><tr className="bg-muted/40">
                <th className={th}>Empresa</th><th className={th}>Sucursal</th>
                <th className={`${th} text-right`}>Actual</th><th className={`${th} text-right`}>Ida</th>
                <th className={`${th} text-right`}>Vuelta</th><th className={`${th} text-right`}>Total</th>
                <th className={th}>Ubicación</th><th className={th}>Acción</th>
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
                    <td className={td}><Badge variant={f.accion === "crear" ? "info" : "accent"}>{f.accion === "crear" ? "nueva" : "actualiza"}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <BrandButton loading={aplicando} onClick={() => setConfirmarAplicar(true)} className="self-start">
            Aplicar a la Tabla KM…
          </BrandButton>
        </div>
      )}

      <BrandModal
        isOpen={confirmarAplicar}
        onClose={() => setConfirmarAplicar(false)}
        title="¿Aplicar estos km a tu Tabla KM?"
        widthPx={460}
      >
        <div className="flex flex-col gap-4">
          <p className="font-body text-sm text-foreground">
            Se van a crear <span className="font-bold">{aCrear}</span> filas nuevas y
            actualizar los km de <span className="font-bold">{aActualizar}</span> existentes.
          </p>
          <p className="font-body text-sm text-muted-foreground">
            El umbral de viático y las observaciones de cada fila <strong>no se tocan</strong>.
            Esta acción no consulta Google (usa el cálculo que ya viste).
          </p>
          <div className="flex justify-end gap-2">
            <BrandButton variant="outline" onClick={() => setConfirmarAplicar(false)}>Cancelar</BrandButton>
            <BrandButton onClick={() => void aplicar()}>Aplicar</BrandButton>
          </div>
        </div>
      </BrandModal>
    </div>
  );
}
