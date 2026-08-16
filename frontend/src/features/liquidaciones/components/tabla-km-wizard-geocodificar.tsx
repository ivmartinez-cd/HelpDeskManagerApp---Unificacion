"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { GeocodificarResultado, SucursalCoordenadas } from "../types/liquidaciones";
import { CandidatosPicker } from "./tabla-km-lugar-modal";

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
            {resultado.noEncontradas > 0 && (
              <Badge variant="warning">{resultado.noEncontradas} no encontradas en Gestión</Badge>
            )}
          </div>
          {resultado.noEncontradas > 0 && resultado.noEncontradasDetalle.length > 0 && (
            <div className="rounded-[6px] border border-warning/30 bg-warning/5 p-3 flex flex-col gap-2">
              <p className="font-body text-xs font-semibold text-foreground">
                ¿Qué significa &quot;no encontradas en Gestión&quot;?
              </p>
              <p className="font-body text-xs text-muted-foreground">
                Estas sucursales están en tu Tabla KM pero no aparecen en Gestión (Siges) con el mismo
                nombre. Puede que hayan cambiado de nombre en Gestión, o que ya no estén asignadas a
                este prestador. Sus domicilios <strong>no se actualizaron</strong> — revisalas y
                corregí el nombre en tu Tabla KM si corresponde.
              </p>
              <div className="flex flex-col gap-0.5 max-h-[12vh] overflow-y-auto">
                {resultado.noEncontradasDetalle.map((f) => (
                  <p key={`${f.empresaNombre}::${f.sucursalNombre}`} className="font-body text-xs text-foreground">
                    <span className="text-muted-foreground">{f.empresaNombre} —</span>{" "}
                    <span className="font-semibold">{f.sucursalNombre}</span>
                  </p>
                ))}
              </div>
            </div>
          )}
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

export function PasoGeocodificar({ prestadorId, resumen, setResumen }: {
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
