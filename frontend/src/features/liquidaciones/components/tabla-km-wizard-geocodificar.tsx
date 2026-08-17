"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type {
  EstadoAsistenteKm, GeocodificarResultado, SucursalCoordenadas,
} from "../types/liquidaciones";
import { CandidatosPicker } from "./tabla-km-lugar-modal";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";

type RefrescarResultado = Awaited<ReturnType<typeof liquidacionesApi.refrescarDatosSucursales>>;

function Tarjeta({ numero, titulo, descripcion, badge, children }: {
  numero: string; titulo: string; descripcion: string;
  badge?: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <div className="rounded-[8px] border border-border p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-body text-sm font-semibold text-foreground">
            <span className="text-brand-orange">{numero}</span> · {titulo}
          </p>
          <p className="font-body text-xs text-muted-foreground">{descripcion}</p>
        </div>
        {badge}
      </div>
      {children}
    </div>
  );
}

function SeccionRefrescarSiges({ prestadorId, onCambio }: {
  prestadorId: string; onCambio: () => void;
}) {
  const [ejecutando, setEjecutando] = useState(false);
  const [resultado, setResultado] = useState<RefrescarResultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ejecutar = async () => {
    setEjecutando(true); setError(null);
    try {
      setResultado(await liquidacionesApi.refrescarDatosSucursales(prestadorId));
      onCambio();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error al refrescar"); }
    finally { setEjecutando(false); }
  };
  return (
    <Tarjeta
      numero="2a"
      titulo="Actualizar datos desde Gestión"
      descripcion="Trae el domicilio actual de cada sucursal y completa el vínculo con Gestión. No consulta Google."
      badge={<Badge variant="success">no usa Google</Badge>}
    >
      <BrandButton size="sm" variant="outline" loading={ejecutando} onClick={ejecutar} className="self-start">
        Actualizar desde Gestión
      </BrandButton>
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      {resultado && (
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">{resultado.actualizadas} direcciones actualizadas</Badge>
            {resultado.vinculadas > 0 && (
              <Badge variant="info">{resultado.vinculadas} vinculadas a Gestión</Badge>
            )}
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
                Estas sucursales están en tu Tabla KM pero no aparecen en Gestión con el mismo
                nombre. Puede que hayan cambiado de nombre, o que ya no estén asignadas a
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
    </Tarjeta>
  );
}

function ResolverPendiente({ prestadorId, fila, onResuelta }: {
  prestadorId: string; fila: SucursalCoordenadas; onResuelta: () => void;
}) {
  const handle = async (body: { candidatoIdx?: number; latitud?: number; longitud?: number }) => {
    await liquidacionesApi.resolverCoordenadas(prestadorId, fila.sigesSucursalId, body);
    toast.success(`${fila.sucursalNombre}: ubicación guardada`);
    onResuelta();
  };
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground">{fila.empresaNombre} — {fila.sucursalNombre}</p>
        <Badge variant={fila.estado === "ambigua" ? "warning" : "neutral"}>
          {fila.estado === "ambigua" ? "elegí una opción" : fila.estado.replaceAll("_", " ")}
        </Badge>
      </div>
      {fila.direccion && <p className="mt-0.5 font-body text-xs text-muted-foreground">{fila.direccion}</p>}
      <div className="mt-2"><CandidatosPicker candidatos={fila.candidatos} onElegir={handle} /></div>
    </div>
  );
}

export function PasoGeocodificar({ prestadorId, estado, onCambio }: {
  prestadorId: string; estado: EstadoAsistenteKm; onCambio: () => void;
}) {
  const [ejecutando, setEjecutando] = useState(false);
  const [resumen, setResumen] = useState<GeocodificarResultado | null>(null);
  const [filas, setFilas] = useState<SucursalCoordenadas[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Las ambiguas persistidas de corridas anteriores se cargan al entrar al
  // paso (DB local, sin Google) — antes solo aparecían tras re-geocodificar.
  const refresh = () =>
    liquidacionesApi.listCoordenadas(prestadorId).then(setFilas).catch(() => setFilas([]));
  useEffect(() => { void refresh(); }, [prestadorId]); // eslint-disable-line react-hooks/exhaustive-deps

  const geocodificar = async () => {
    setEjecutando(true); setError(null);
    try {
      setResumen(await liquidacionesApi.geocodificarFaltantes(prestadorId));
      await refresh();
      onCambio();
    } catch (e: unknown) { setError(e instanceof Error ? e.message : "Error al buscar ubicaciones"); }
    finally { setEjecutando(false); }
  };

  const pendientes = (filas ?? []).filter((f) => f.estado === "ambigua");

  return (
    <div className="flex flex-col gap-4">
      <SeccionRefrescarSiges prestadorId={prestadorId} onCambio={onCambio} />

      <Tarjeta
        numero="2b"
        titulo="Buscar ubicaciones faltantes"
        descripcion="Busca en el mapa las sucursales que no tienen ubicación en Gestión. Las inequívocas se guardan solas; las dudosas pasan al punto 2c."
      >
        {estado.sinCoordenadas === 0 && !resumen ? (
          <p className="font-body text-sm text-muted-foreground italic">
            ✓ Todas las sucursales activas tienen ubicación — nada que buscar.
          </p>
        ) : (
          <BotonConsumoGoogle
            estimacion={estado.estimacionGeocodificar}
            tope={estado.topePorCorrida}
            loading={ejecutando}
            onEjecutar={geocodificar}
          >
            Buscar ubicaciones ({estado.sinCoordenadas} sucursales)
          </BotonConsumoGoogle>
        )}
        {error && <p className="font-body text-sm text-destructive">{error}</p>}
        {resumen && (
          <div className="flex flex-wrap gap-2">
            <Badge variant="success">{resumen.resueltasAuto} resueltas solas</Badge>
            <Badge variant="warning">{resumen.ambiguas} para elegir en 2c</Badge>
            <Badge variant="neutral">{resumen.sinResultados} sin resultado</Badge>
            <Badge variant="neutral">{resumen.sinDireccion} sin dirección escrita</Badge>
            <Badge variant="info">{resumen.llamadasGoogle} consultas usadas</Badge>
            {resumen.pendientesPorTope > 0 && <Badge variant="danger">{resumen.pendientesPorTope} cortadas por tope</Badge>}
          </div>
        )}
      </Tarjeta>

      <Tarjeta
        numero="2c"
        titulo="Elegir la ubicación correcta"
        descripcion="Google devolvió más de una opción para estas direcciones. Elegir no consulta Google."
      >
        {pendientes.length > 0 ? (
          <div className="flex max-h-[32vh] flex-col gap-3 overflow-y-auto pr-1">
            {pendientes.map((f) => (
              <ResolverPendiente
                key={f.sigesSucursalId}
                prestadorId={prestadorId}
                fila={f}
                onResuelta={() => { void refresh(); onCambio(); }}
              />
            ))}
          </div>
        ) : (
          <p className="font-body text-sm text-muted-foreground italic">
            {filas === null ? "Cargando…" : "✓ No hay direcciones pendientes de elección."}
          </p>
        )}
      </Tarjeta>
    </div>
  );
}
