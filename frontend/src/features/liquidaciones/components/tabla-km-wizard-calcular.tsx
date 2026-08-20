"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  AplicarDistanciasResult, CalculoKmPreview, EstadoAsistenteKm, PrestadorLiquidacion,
} from "../types/liquidaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";
import { Aviso } from "./tabla-km-wizard-ui";

/** Origen del pin usado para el cálculo, en llano. */
const LABEL_COORDS_ORIGEN: Record<string, string> = {
  siges: "Gestión",
  geocode: "Google",
  manual: "Manual",
};
const th = "py-2 px-3 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const td = "py-1.5 px-3 font-body text-[13px]";

function TablaPreview({ preview }: { preview: CalculoKmPreview }) {
  return (
    <div className="max-h-[32vh] overflow-y-auto rounded-[8px] border border-border">
      <table className="w-full">
        <thead className="sticky top-0 bg-card"><tr className="bg-muted/40">
          <th className={th}>Empresa</th><th className={th}>Sucursal</th>
          <th className={`${th} text-right`}>Actual</th><th className={`${th} text-right`}>Ida</th>
          <th className={`${th} text-right`}>Vuelta</th><th className={`${th} text-right`}>Total</th>
          <th className={th}>Origen del pin</th><th className={th}>Acción</th>
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
  );
}

function ResumenPreview({ preview }: { preview: CalculoKmPreview }) {
  const aCrear = preview.filas.filter((f) => f.accion === "crear").length;
  const aActualizar = preview.filas.filter((f) => f.accion === "actualizar").length;
  return (
    <p className="font-body text-sm text-foreground">
      {aCrear} filas nuevas · {aActualizar} a actualizar · {preview.sinUbicar} sin ubicar
      {preview.sinRuta > 0 && ` · ${preview.sinRuta} sin ruta`}
      {preview.sinActividad > 0 && ` · ${preview.sinActividad} ex-clientes omitidos`}
      {" "}· {preview.elementosGoogle} consultas usadas
    </p>
  );
}

/** Momento 3. NUNCA consulta Google al entrar: muestra el resumen y recién
 * calcula cuando el operador confirma el costo. Preview con diff → aplicar. */
export function MomentoCalcular({ prestador, estado, preview, setPreview, onAplicado, irARevisar }: {
  prestador: PrestadorLiquidacion;
  estado: EstadoAsistenteKm;
  preview: CalculoKmPreview | null;
  setPreview: (p: CalculoKmPreview | null) => void;
  onAplicado: (resultado: AplicarDistanciasResult) => Promise<void>;
  irARevisar: () => void;
}) {
  const [calculando, setCalculando] = useState(false);
  const [aplicando, setAplicando] = useState(false);
  const [confirmarAplicar, setConfirmarAplicar] = useState(false);
  const [calcularIgual, setCalcularIgual] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calcular = async () => {
    setCalculando(true); setError(null);
    try { setPreview(await liquidacionesApi.previewCalcularDistancias(prestador.id)); }
    catch (e: unknown) { setError(e instanceof Error ? e.message : "No se pudieron calcular las distancias"); }
    finally { setCalculando(false); }
  };

  const aplicar = async () => {
    if (!preview) return;
    setConfirmarAplicar(false);
    setAplicando(true);
    try {
      const res = await liquidacionesApi.aplicarCalcularDistancias(prestador.id, preview.id);
      toast.success(`Listo: ${res.creadas} filas creadas, ${res.actualizadas} actualizadas`);
      setPreview(null);
      await onAplicado(res);
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "No se pudieron aplicar los km"); }
    finally { setAplicando(false); }
  };

  const aCrear = preview?.filas.filter((f) => f.accion === "crear").length ?? 0;
  const aActualizar = preview?.filas.filter((f) => f.accion === "actualizar").length ?? 0;
  const gateSinUbicar = estado.sinCoordenadas > 0 && !calcularIgual && !preview;

  return (
    <div className="flex flex-col gap-4">
      {!preview && (
        <p className="font-body text-sm text-muted-foreground">
          Se van a calcular los km de ida y vuelta (con Google Maps) para{" "}
          <span className="font-semibold text-foreground">{estado.estimacionDistancias / 2} sucursales con ubicación</span>.
          Primero ves el resultado; nada se guarda hasta que apliques.
        </p>
      )}

      {gateSinUbicar && (
        <Aviso tono="alerta">
          <p className="font-semibold">Hay {estado.sinCoordenadas} sucursales sin ubicación en el mapa.</p>
          <p className="text-muted-foreground">Si calculás ahora, esas {estado.sinCoordenadas} van a quedar <strong>sin km</strong>. Lo recomendado es resolverlas primero.</p>
          <div className="mt-2 flex flex-wrap gap-2">
            <BrandButton size="sm" onClick={irARevisar}>Resolverlas primero (recomendado)</BrandButton>
            <BrandButton size="sm" variant="outline" onClick={() => setCalcularIgual(true)}>
              Calcular igual — las {estado.sinCoordenadas} quedan sin km
            </BrandButton>
          </div>
        </Aviso>
      )}

      {!preview && !gateSinUbicar && (
        <BotonConsumoGoogle estimacion={estado.estimacionDistancias} tope={estado.topePorCorrida} bloquearSobreTope loading={calculando} onEjecutar={calcular}>
          Calcular km
        </BotonConsumoGoogle>
      )}

      {error && <p className="font-body text-sm text-destructive">{error}</p>}

      {preview && (
        <div className="flex flex-col gap-3">
          <ResumenPreview preview={preview} />
          <TablaPreview preview={preview} />
          <BrandButton loading={aplicando} onClick={() => setConfirmarAplicar(true)} className="self-start">
            Aplicar a la Tabla KM…
          </BrandButton>
        </div>
      )}

      <BrandModal isOpen={confirmarAplicar} onClose={() => setConfirmarAplicar(false)} title="¿Aplicar estos km a tu Tabla KM?" widthPx={460}>
        <div className="flex flex-col gap-4">
          <p className="font-body text-sm text-foreground">
            Se van a crear <span className="font-bold">{aCrear}</span> filas nuevas y actualizar los km de{" "}
            <span className="font-bold">{aActualizar}</span> existentes.
          </p>
          <p className="font-body text-sm text-muted-foreground">
            El umbral de viático y las observaciones de cada fila <strong>no se tocan</strong>. Esta acción no consulta Google (usa el cálculo que ya viste).
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
