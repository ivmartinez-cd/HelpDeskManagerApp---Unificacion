"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { cn } from "@/shared/utils/cn";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  CalculoKmPreview, GeocodificarResultado, PinSospechoso,
  PrestadorLiquidacion, SucursalCoordenadas,
} from "../types/liquidaciones";
import { CandidatosPicker } from "./tabla-km-lugar-modal";

const PASOS = ["Geocodificar", "Distancias", "Pines"] as const;
const LABEL_COORDS_ORIGEN: Record<string, string> = {
  siges: "Siges",
  geocode: "Geocodificado",
  manual: "Manual",
};
type Paso = 0 | 1 | 2;
const th = "py-2 px-3 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const td = "py-1.5 px-3 font-body text-[13px]";

function Indicador({ actual }: { actual: Paso }) {
  return (
    <div className="mb-6 flex items-center justify-center">
      {PASOS.map((nombre, i) => (
        <div key={nombre} className="flex items-center">
          <div className="flex flex-col items-center gap-1">
            <div className={cn(
              "flex h-8 w-8 items-center justify-center rounded-full font-heading text-sm font-bold transition-colors",
              i < actual && "bg-brand-orange/20 text-brand-orange",
              i === actual && "bg-brand-orange text-white",
              i > actual && "border-2 border-border text-muted-foreground",
            )}>
              {i < actual ? "✓" : i + 1}
            </div>
            <span className={cn("font-body text-[10px] font-bold uppercase tracking-[.06em]",
              i === actual ? "text-brand-orange" : "text-muted-foreground"
            )}>{nombre}</span>
          </div>
          {i < 2 && <div className={cn("mb-5 mx-3 h-[2px] w-16 flex-shrink-0 rounded-full transition-colors",
            i < actual ? "bg-brand-orange/40" : "bg-border")} />}
        </div>
      ))}
    </div>
  );
}

function ResolverPendiente({ prestadorId, fila, onResuelta }: {
  prestadorId: string; fila: SucursalCoordenadas; onResuelta: () => void;
}) {
  const handle = async (body: { candidatoIdx?: number; latitud?: number; longitud?: number }) => {
    await liquidacionesApi.resolverCoordenadas(prestadorId, fila.sigesSucursalId, body);
    toast.success(`${fila.sucursalNombre}: coordenadas guardadas`);
    onResuelta();
  };
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">{fila.empresaNombre} — {fila.sucursalNombre}</p>
        <Badge variant={fila.estado === "ambigua" ? "warning" : "neutral"}>{fila.estado}</Badge>
      </div>
      {fila.direccion && <p className="mt-0.5 font-body text-xs text-muted-foreground">{fila.direccion}</p>}
      <div className="mt-2"><CandidatosPicker candidatos={fila.candidatos} onElegir={handle} /></div>
    </div>
  );
}

type RefrescarResultado = Awaited<ReturnType<typeof liquidacionesApi.refrescarDatosSucursales>>;

function SeccionRefrescarSiges({ prestadorId }: { prestadorId: string }) {
  const [ejecutando, setEjecutando] = useState(false);
  const [resultado, setResultado] = useState<RefrescarResultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ejecutar = async () => {
    setEjecutando(true); setError(null);
    try {
      setResultado(await liquidacionesApi.refrescarDatosSucursales(prestadorId));
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error al refrescar"); }
    finally { setEjecutando(false); }
  };
  return (
    <div className="rounded-[8px] border border-border p-4 flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="font-body text-sm font-semibold text-foreground">Actualizar datos desde Gestión</p>
          <p className="font-body text-xs text-muted-foreground">Sincroniza domicilio, localidad y provincia de cada sucursal con los datos actuales de Siges.</p>
        </div>
        <BrandButton size="sm" variant="outline" loading={ejecutando} onClick={ejecutar}>
          Actualizar desde Siges
        </BrandButton>
      </div>
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      {resultado && (
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">{resultado.actualizadas} actualizadas</Badge>
            <Badge variant="neutral">{resultado.sinCambios} sin cambios</Badge>
            {resultado.noEncontradas > 0 && <Badge variant="warning">{resultado.noEncontradas} no encontradas en Siges</Badge>}
          </div>
          {resultado.cambios.length > 0 && (
            <div className="flex max-h-[15vh] flex-col gap-1 overflow-y-auto text-xs font-body text-muted-foreground">
              {resultado.cambios.map((c) => (
                <p key={`${c.empresaNombre}::${c.sucursalNombre}`}>
                  <span className="font-semibold text-foreground">{c.sucursalNombre}</span>:{" "}
                  <span className="line-through">{c.domicilioAntes ?? "—"}</span> → {c.domicilioDespues ?? "—"}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PasoGeocodificar({ prestadorId, resumen, setResumen }: {
  prestadorId: string; resumen: GeocodificarResultado | null;
  setResumen: (r: GeocodificarResultado) => void;
}) {
  const [ejecutando, setEjecutando] = useState(false);
  const [filas, setFilas] = useState<SucursalCoordenadas[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const refresh = async () => setFilas(await liquidacionesApi.listCoordenadas(prestadorId));
  const ejecutar = async () => {
    setEjecutando(true); setError(null);
    try {
      const r = await liquidacionesApi.geocodificarFaltantes(prestadorId);
      setResumen(r);
      await refresh();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error al geocodificar"); }
    finally { setEjecutando(false); }
  };
  const pendientes = (filas ?? []).filter((f) => f.estado !== "resuelta");
  return (
    <div className="flex flex-col gap-4">
      <SeccionRefrescarSiges prestadorId={prestadorId} />
      <p className="font-body text-sm text-muted-foreground">
        Después de actualizar, geocodificá las sucursales sin coordenadas en Siges.
        Las ambiguas quedan listadas para que elijas el candidato correcto.
      </p>
      {error && !resumen && <p className="font-body text-sm text-destructive">{error}</p>}
      {!resumen ? (
        <BrandButton loading={ejecutando} onClick={ejecutar}>Geocodificar sucursales faltantes</BrandButton>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">{resumen.resueltasAuto} resueltas</Badge>
            <Badge variant="warning">{resumen.ambiguas} ambiguas</Badge>
            <Badge variant="neutral">{resumen.sinResultados} sin resultado</Badge>
            <Badge variant="neutral">{resumen.sinDireccion} sin dirección</Badge>
            <Badge variant="neutral">{resumen.yaResueltas} ya resueltas</Badge>
            <Badge variant="info">{resumen.llamadasGoogle} llamadas Google</Badge>
            {resumen.pendientesPorTope > 0 && <Badge variant="danger">{resumen.pendientesPorTope} cortadas por tope</Badge>}
          </div>
          {pendientes.length > 0 ? (
            <div className="flex max-h-[35vh] flex-col gap-3 overflow-y-auto pr-1">
              {pendientes.map((f) => <ResolverPendiente key={f.sigesSucursalId} prestadorId={prestadorId} fila={f} onResuelta={refresh} />)}
            </div>
          ) : (
            <p className="font-body text-sm text-muted-foreground italic">Todas las sucursales tienen coordenadas. Podés pasar al siguiente paso.</p>
          )}
        </div>
      )}
    </div>
  );
}

function PasoCalcular({ prestador, preview, setPreview, onAplicado }: {
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

function PasoPines({ prestadorId }: { prestadorId: string }) {
  const [pines, setPines] = useState<PinSospechoso[] | null>(null);
  const [auditando, setAuditando] = useState(false);
  const [key, setKey] = useState(0);
  useEffect(() => {
    liquidacionesApi.listPinesSospechosos(prestadorId).then(setPines).catch(() => setPines([]));
  }, [prestadorId, key]);
  const auditar = async () => {
    setAuditando(true);
    try {
      const r = await liquidacionesApi.auditarPines(prestadorId);
      toast.success(`${r.geocodificadas} geocodificadas (${r.llamadasGoogle} llamadas Google)`);
      setKey(k => k + 1);
    } finally { setAuditando(false); }
  };
  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Revisá si algún pin de Siges difiere del geocode del domicilio (umbral: 5 km).
        &quot;Usar geocode&quot; corrige las coordenadas para el próximo cálculo de km.
        Este paso es opcional — podés finalizar sin auditarlo.
      </p>
      {!pines ? (
        <div className="flex h-20 items-center justify-center"><Spinner /></div>
      ) : pines.length === 0 ? (
        <p className="font-body text-sm text-muted-foreground italic">Sin discrepancias detectadas. Usá &quot;Auditar con Google&quot; para geocodificar domicilios faltantes.</p>
      ) : (
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
      )}
      <BrandButton variant="outline" size="sm" loading={auditando} onClick={auditar}>Auditar con Google</BrandButton>
    </div>
  );
}

export function TablaKmWizard({
  prestador, onClose, onAplicado,
}: {
  prestador: PrestadorLiquidacion; onClose: () => void; onAplicado: () => void;
}) {
  const [paso, setPaso] = useState<Paso>(0);
  const [geoResumen, setGeoResumen] = useState<GeocodificarResultado | null>(null);
  const [preview, setPreview] = useState<CalculoKmPreview | null>(null);
  const ir = (n: number) => setPaso(Math.max(0, Math.min(2, n)) as Paso);

  return (
    <BrandModal isOpen onClose={onClose} title={`Configurar km — ${prestador.nombreCorto}`} widthPx={900}>
      <Indicador actual={paso} />
      <div className="min-h-[300px]">
        {paso === 0 && <PasoGeocodificar prestadorId={prestador.id} resumen={geoResumen} setResumen={setGeoResumen} />}
        {paso === 1 && <PasoCalcular prestador={prestador} preview={preview} setPreview={setPreview} onAplicado={onAplicado} />}
        {paso === 2 && <PasoPines prestadorId={prestador.id} />}
      </div>
      <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
        {paso < 2 ? (
          <button className="font-body text-sm text-muted-foreground hover:text-foreground" onClick={() => ir(paso + 1)}>
            Omitir este paso →
          </button>
        ) : <span />}
        <div className="flex gap-2">
          {paso > 0 && <BrandButton variant="outline" onClick={() => ir(paso - 1)}>← Anterior</BrandButton>}
          {paso < 2
            ? <BrandButton onClick={() => ir(paso + 1)}>Siguiente →</BrandButton>
            : <BrandButton onClick={onClose}>Finalizar</BrandButton>}
        </div>
      </div>
    </BrandModal>
  );
}
