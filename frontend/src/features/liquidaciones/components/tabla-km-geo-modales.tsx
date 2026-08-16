"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  CalculoKmPreview,
  GeocodificarResultado,
  PrestadorLiquidacion,
  SucursalCoordenadas,
} from "../types/liquidaciones";
import { CandidatosPicker } from "./tabla-km-lugar-modal";

const thCls =
  "py-2 px-3 font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground text-left";
const tdCls = "py-1.5 px-3 font-body text-[13px] text-foreground";

/** Cálculo masivo en dos pasos: al abrir corre el preview (llama a Google una
 * sola vez); nada se persiste en tabla_km hasta confirmar con "Aplicar". */
export function CalcularDistanciasModal({
  prestador,
  onClose,
  onAplicado,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
  onAplicado: () => void;
}) {
  const [preview, setPreview] = useState<CalculoKmPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [aplicando, setAplicando] = useState(false);

  useEffect(() => {
    liquidacionesApi
      .previewCalcularDistancias(prestador.id)
      .then(setPreview)
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Error al generar el preview"),
      );
  }, [prestador.id]);

  const handleAplicar = async () => {
    if (!preview) return;
    setAplicando(true);
    setError(null);
    try {
      const res = await liquidacionesApi.aplicarCalcularDistancias(prestador.id, preview.id);
      toast.success(`Aplicado: ${res.creadas} creadas, ${res.actualizadas} actualizadas`);
      onAplicado();
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al aplicar");
      setAplicando(false);
    }
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={`Calcular distancias — ${prestador.nombreCorto}`}
      error={error}
      widthPx={860}
    >
      {!preview && !error ? (
        <div className="flex h-40 flex-col items-center justify-center gap-3">
          <Spinner />
          <p className="font-body text-sm text-muted-foreground">
            Consultando Google Maps (ida y vuelta por sucursal)...
          </p>
        </div>
      ) : preview ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="info">
              {preview.filas.filter((f) => f.accion === "crear").length} a crear
            </Badge>
            <Badge variant="accent">
              {preview.filas.filter((f) => f.accion === "actualizar").length} a actualizar
            </Badge>
            <Badge variant="neutral">{preview.sinUbicar} sin ubicar</Badge>
            {preview.sinRuta > 0 && <Badge variant="warning">{preview.sinRuta} sin ruta</Badge>}
            <Badge variant="neutral">{preview.elementosGoogle} llamadas Google</Badge>
          </div>
          <div className="max-h-[52vh] overflow-y-auto rounded-[8px] border border-border">
            <table className="w-full">
              <thead className="sticky top-0 bg-card">
                <tr className="bg-muted/40">
                  <th className={thCls}>Empresa</th>
                  <th className={thCls}>Sucursal</th>
                  <th className={`${thCls} text-right`}>Actual</th>
                  <th className={`${thCls} text-right`}>Ida</th>
                  <th className={`${thCls} text-right`}>Vuelta</th>
                  <th className={`${thCls} text-right`}>Total nuevo</th>
                  <th className={thCls}>Coords</th>
                  <th className={thCls}>Acción</th>
                </tr>
              </thead>
              <tbody>
                {preview.filas.map((f) => (
                  <tr
                    key={`${f.empresaNombre}::${f.sucursalNombre}`}
                    className="border-t border-border"
                  >
                    <td className={tdCls}>
                      <span className="block max-w-[160px] truncate" title={f.empresaNombre}>
                        {f.empresaNombre}
                      </span>
                    </td>
                    <td className={tdCls}>
                      <span className="block max-w-[200px] truncate" title={f.sucursalNombre}>
                        {f.sucursalNombre}
                      </span>
                    </td>
                    <td className={`${tdCls} text-right tabular-nums text-muted-foreground`}>
                      {f.kmsRecorridoActual != null ? f.kmsRecorridoActual.toFixed(1) : "—"}
                    </td>
                    <td className={`${tdCls} text-right tabular-nums`}>{f.kmsIda.toFixed(1)}</td>
                    <td className={`${tdCls} text-right tabular-nums`}>
                      {f.kmsVuelta.toFixed(1)}
                    </td>
                    <td className={`${tdCls} text-right tabular-nums font-semibold`}>
                      {f.kmsTotal.toFixed(1)}
                    </td>
                    <td className={tdCls}>
                      <Badge variant={f.coordsOrigen === "siges" ? "neutral" : "info"}>
                        {f.coordsOrigen}
                      </Badge>
                    </td>
                    <td className={tdCls}>
                      <Badge variant={f.accion === "crear" ? "info" : "accent"}>{f.accion}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex justify-end gap-3">
            <BrandButton variant="outline" onClick={onClose}>
              Cancelar
            </BrandButton>
            <BrandButton loading={aplicando} onClick={handleAplicar}>
              Aplicar {preview.filas.length} cambios
            </BrandButton>
          </div>
        </div>
      ) : (
        <div className="flex justify-end">
          <BrandButton variant="outline" onClick={onClose}>
            Cerrar
          </BrandButton>
        </div>
      )}
    </BrandModal>
  );
}

/** Geocodifica sucursales sin pin en Siges y deja revisar/resolver ambiguas. */
export function GeocodificarModal({
  prestador,
  onClose,
}: {
  prestador: PrestadorLiquidacion;
  onClose: () => void;
}) {
  const [resumen, setResumen] = useState<GeocodificarResultado | null>(null);
  const [filas, setFilas] = useState<SucursalCoordenadas[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    liquidacionesApi
      .geocodificarFaltantes(prestador.id)
      .then(async (r) => {
        setResumen(r);
        setFilas(await liquidacionesApi.listCoordenadas(prestador.id));
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : "Error al geocodificar"),
      );
  }, [prestador.id]);

  const refresh = async () => {
    setFilas(await liquidacionesApi.listCoordenadas(prestador.id));
  };

  const pendientes = (filas ?? []).filter((f) => f.estado !== "resuelta");

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={`Geocodificar faltantes — ${prestador.nombreCorto}`}
      error={error}
      widthPx={720}
    >
      {!resumen && !error ? (
        <div className="flex h-40 flex-col items-center justify-center gap-3">
          <Spinner />
          <p className="font-body text-sm text-muted-foreground">
            Geocodificando sucursales sin coordenadas...
          </p>
        </div>
      ) : resumen ? (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">{resumen.resueltasAuto} resueltas solas</Badge>
            <Badge variant="warning">{resumen.ambiguas} ambiguas</Badge>
            <Badge variant="neutral">{resumen.sinResultados} sin resultados</Badge>
            <Badge variant="neutral">{resumen.sinDireccion} sin dirección</Badge>
            <Badge variant="neutral">{resumen.yaResueltas} ya resueltas</Badge>
            <Badge variant="info">{resumen.llamadasGoogle} llamadas Google</Badge>
            {resumen.pendientesPorTope > 0 && (
              <Badge variant="danger">{resumen.pendientesPorTope} cortadas por tope</Badge>
            )}
          </div>
          {pendientes.length > 0 ? (
            <div className="flex max-h-[50vh] flex-col gap-3 overflow-y-auto pr-1">
              {pendientes.map((f) => (
                <ResolverPendiente
                  key={f.sigesSucursalId}
                  prestadorId={prestador.id}
                  fila={f}
                  onResuelta={refresh}
                />
              ))}
            </div>
          ) : (
            <p className="font-body text-sm text-muted-foreground italic">
              No quedan sucursales pendientes de revisión.
            </p>
          )}
          <div className="flex justify-end">
            <BrandButton variant="outline" onClick={onClose}>
              Cerrar
            </BrandButton>
          </div>
        </div>
      ) : (
        <div className="flex justify-end">
          <BrandButton variant="outline" onClick={onClose}>
            Cerrar
          </BrandButton>
        </div>
      )}
    </BrandModal>
  );
}

function ResolverPendiente({
  prestadorId,
  fila,
  onResuelta,
}: {
  prestadorId: string;
  fila: SucursalCoordenadas;
  onResuelta: () => void;
}) {
  const handleResolver = async (body: {
    candidatoIdx?: number;
    latitud?: number;
    longitud?: number;
  }) => {
    await liquidacionesApi.resolverCoordenadas(prestadorId, fila.sigesSucursalId, body);
    toast.success(`${fila.sucursalNombre}: coordenadas guardadas`);
    onResuelta();
  };

  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">
          {fila.empresaNombre} — {fila.sucursalNombre}
        </p>
        <Badge variant={fila.estado === "ambigua" ? "warning" : "neutral"}>{fila.estado}</Badge>
      </div>
      {fila.direccion && (
        <p className="mt-0.5 font-body text-xs text-muted-foreground">{fila.direccion}</p>
      )}
      <div className="mt-2">
        <CandidatosPicker candidatos={fila.candidatos} onElegir={handleResolver} />
      </div>
    </div>
  );
}
