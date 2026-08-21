"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { DatosAsistente } from "../hooks/use-asistente-km";
import type { FilaNoEncontrada } from "../lib/asistente-km-bandeja";
import { plural } from "../lib/asistente-km-textos";
import type { EstadoAsistenteKm, ResultadoAutoVinculoN1, SucursalSiges } from "../types/liquidaciones";
import { Aviso, Resultado, VerDetalle } from "./tabla-km-wizard-ui";

type Refresco = Awaited<ReturnType<typeof liquidacionesApi.refrescarDatosSucursales>>;
type Etapa = "domicilios" | "nombres" | "importar" | null;

interface ResultadoTraer { refresco: Refresco; n1: ResultadoAutoVinculoN1; importadas: number }

/** Bloqueantes que se resuelven afuera del asistente (Configuración / Gestión). */
export function Bloqueantes({ estado, nombrePrestador }: { estado: EstadoAsistenteKm; nombrePrestador: string }) {
  if (!estado.vinculadoSiges) {
    return (
      <Aviso tono="bloqueo">
        <strong>Este prestador no está vinculado a Gestión.</strong> Sin ese vínculo el asistente no
        puede leer sus sucursales. Se configura en Configuración → Prestadores → {nombrePrestador} → Vincular.
      </Aviso>
    );
  }
  if (!estado.baseConfigurada) {
    return (
      <Aviso tono="bloqueo">
        <strong>Falta la sucursal base de despacho.</strong> Es el punto desde donde sale el técnico — sin ella no
        se pueden calcular km. Se configura en Configuración → Prestadores → {nombrePrestador}, campo Sucursal base.
      </Aviso>
    );
  }
  if (!estado.baseConCoordenadas) {
    return (
      <Aviso tono="bloqueo">
        <strong>La sucursal base no tiene ubicación en Gestión.</strong> Su latitud y longitud están vacías o en
        cero. Hay que cargar las coordenadas reales en Gestión, en la sucursal del prestador.
      </Aviso>
    );
  }
  return null;
}

function ListaSucursales({ sucursales }: { sucursales: SucursalSiges[] }) {
  return (
    <ul className="max-h-[24vh] overflow-y-auto flex flex-col gap-1">
      {sucursales.map((s) => (
        <li key={s.sigesSucursalId} className="font-body text-xs">
          <span className="font-semibold text-foreground">{s.empresaNombre} · {s.sucursalNombre}</span>
          <span className="text-muted-foreground"> — {[s.domicilio, s.localidad, s.provincia].filter(Boolean).join(" · ") || "sin domicilio en Gestión"}</span>
          {!s.actividadReciente && <span className="text-muted-foreground"> · ex-cliente</span>}
        </li>
      ))}
    </ul>
  );
}

function agruparPorEmpresa(filas: FilaNoEncontrada[]): [string, string[]][] {
  const grupos = new Map<string, string[]>();
  for (const f of filas) grupos.set(f.empresaNombre, [...(grupos.get(f.empresaNombre) ?? []), f.sucursalNombre]);
  return [...grupos.entries()].sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]));
}

function ListaNoEncontradas({ filas }: { filas: FilaNoEncontrada[] }) {
  return (
    <ul className="max-h-[28vh] overflow-y-auto rounded-[6px] border border-border bg-card px-3 py-2 flex flex-col gap-1.5">
      {agruparPorEmpresa(filas).map(([empresa, sucursales]) => (
        <li key={empresa}>
          <p className="font-semibold text-foreground">{empresa} <span className="font-normal text-muted-foreground">({sucursales.length})</span></p>
          <ul className="ml-3 flex flex-col">
            {sucursales.sort((a, b) => a.localeCompare(b)).map((s) => <li key={s}>{s}</li>)}
          </ul>
        </li>
      ))}
    </ul>
  );
}

function ListaCambios({ cambios }: { cambios: Refresco["cambios"] }) {
  return (
    <ul className="max-h-[24vh] overflow-y-auto rounded-[6px] border border-border bg-card px-3 py-2 flex flex-col gap-1">
      {cambios.map((c) => (
        <li key={`${c.empresaNombre}::${c.sucursalNombre}`}>
          <span className="font-semibold text-foreground">{c.empresaNombre} — {c.sucursalNombre}</span>:{" "}
          <span className="line-through">{c.domicilioAntes ?? "—"}</span> → {c.domicilioDespues ?? "—"}
        </li>
      ))}
    </ul>
  );
}

function ResumenTraido({ r }: { r: ResultadoTraer }) {
  const { refresco, n1 } = r;
  return (
    <div className="flex flex-col gap-2">
      <Resultado>
        Listo: actualizamos {plural(refresco.actualizadas, "domicilio", "domicilios")}
        {refresco.vinculadas > 0 && `, completamos ${plural(refresco.vinculadas, "vínculo", "vínculos")}`}
        , importamos {plural(r.importadas, "sucursal", "sucursales")} y vinculamos {n1.vinculadas} por nombre automáticamente.
      </Resultado>
      {refresco.noEncontradas > 0 && (
        <p className="font-body text-sm text-muted-foreground">
          {plural(refresco.noEncontradas, "fila de tu tabla no aparece", "filas de tu tabla no aparecen")} en Gestión
          — están en Revisar pendientes.
        </p>
      )}
      <VerDetalle etiqueta="ver qué cambió">
        <div className="flex flex-col gap-3">
          <p>{plural(refresco.sinCambios, "fila sin cambios", "filas sin cambios")} · {n1.sinCambios} nombres ya estaban al día.</p>
          {refresco.cambios.length > 0 && (
            <div className="flex flex-col gap-1">
              <p className="font-semibold text-foreground">Domicilios actualizados ({refresco.cambios.length})</p>
              <ListaCambios cambios={refresco.cambios} />
            </div>
          )}
          {refresco.noEncontradasDetalle.length > 0 && (
            <div className="flex flex-col gap-1">
              <p className="font-semibold text-foreground">
                No encontradas en Gestión ({refresco.noEncontradasDetalle.length}) — sus domicilios no se actualizaron
              </p>
              <ListaNoEncontradas filas={refresco.noEncontradasDetalle} />
            </div>
          )}
        </div>
      </VerDetalle>
    </div>
  );
}

const LABEL_ETAPA: Record<Exclude<Etapa, null>, string> = {
  domicilios: "Actualizando domicilios…", nombres: "Vinculando nombres…", importar: "Importando…",
};

async function importarSucursales(prestadorId: string, nuevas: SucursalSiges[], onProgreso: (i: number) => void) {
  for (const [i, s] of nuevas.entries()) {
    await liquidacionesApi.createTablaKm({
      prestadorId,
      empresaNombre: s.empresaNombre,
      sucursalNombre: s.sucursalNombre,
      domicilioCliente: s.domicilio ?? undefined,
      localidadCliente: s.localidad ?? undefined,
      provinciaCliente: s.provincia ?? undefined,
      kmsRecorrido: 0,
      umbralViatico: 30,
      aplicaViatico: false,
    });
    onProgreso(i + 1);
  }
}

/** Momento 1: una sola acción gratis que agrupa refrescar + vincular por nombre +
 * importar las nuevas con actividad (decisión 0.4.e). */
export function MomentoTraer({ prestadorId, nombrePrestador, datos, onCambio, registrarNoEncontradas, irARevisar }: {
  prestadorId: string;
  nombrePrestador: string;
  datos: DatosAsistente;
  onCambio: () => Promise<void>;
  registrarNoEncontradas: (filas: FilaNoEncontrada[]) => void;
  irARevisar: () => void;
}) {
  const [etapa, setEtapa] = useState<Etapa>(null);
  const [progreso, setProgreso] = useState(0);
  const [incluirEx, setIncluirEx] = useState(false);
  const [resultado, setResultado] = useState<ResultadoTraer | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { estado, sucursalesSiges } = datos;
  const nuevasActivas = sucursalesSiges.filter((s) => !s.yaCargada && s.actividadReciente);
  const nuevasEx = sucursalesSiges.filter((s) => !s.yaCargada && !s.actividadReciente);
  const aImportar = incluirEx ? [...nuevasActivas, ...nuevasEx] : nuevasActivas;

  const traer = async () => {
    setError(null);
    try {
      setEtapa("domicilios");
      const refresco = await liquidacionesApi.refrescarDatosSucursales(prestadorId);
      registrarNoEncontradas(refresco.noEncontradasDetalle);
      setEtapa("nombres");
      const n1 = await liquidacionesApi.autoVincularN1(prestadorId);
      setEtapa("importar");
      setProgreso(0);
      await importarSucursales(prestadorId, aImportar, setProgreso);
      setResultado({ refresco, n1, importadas: aImportar.length });
      toast.success("Datos traídos de Gestión");
      await onCambio();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "No se pudo traer de Gestión. Probá de nuevo.");
    } finally { setEtapa(null); }
  };

  if (!estado.vinculadoSiges) return <Bloqueantes estado={estado} nombrePrestador={nombrePrestador} />;

  return (
    <div className="flex flex-col gap-4">
      <Bloqueantes estado={estado} nombrePrestador={nombrePrestador} />
      <p className="font-body text-sm text-foreground">
        Gestión tiene <strong>{plural(estado.sucursalesActivas, "sucursal activa", "sucursales activas")}</strong> de
        este prestador. Tu Tabla KM tiene <strong>{plural(estado.filasTablaKm, "fila", "filas")}</strong>.
      </p>
      {resultado ? <ResumenTraido r={resultado} /> : (
        <>
          <div className="font-body text-sm text-foreground">
            <p>Al traer de Gestión vamos a:</p>
            <ul className="mt-1 list-disc pl-5 text-muted-foreground flex flex-col gap-0.5">
              <li>actualizar domicilios y vínculos de las {estado.filasTablaKm} filas</li>
              <li>importar {plural(aImportar.length, "sucursal nueva", "sucursales nuevas")}{incluirEx ? " (incluidos ex-clientes)" : " con actividad"}</li>
              <li>vincular automáticamente los nombres que solo difieren en un símbolo o una abreviatura</li>
            </ul>
            <p className="mt-1 text-muted-foreground">No consulta Google.</p>
          </div>
          <div className="flex items-center gap-3">
            <BrandButton loading={etapa !== null} onClick={traer} disabled={etapa !== null}>
              {etapa === "importar" ? `Importando ${progreso}/${aImportar.length}…` : etapa ? LABEL_ETAPA[etapa] : "Traer de Gestión"}
            </BrandButton>
          </div>
          {error && <p className="font-body text-sm text-destructive">{error}</p>}
          <VerDetalle etiqueta="ver detalle">
            <p>
              &quot;Con actividad&quot; = clientes con liquidaciones en los últimos 24 meses. Las sucursales se crean en tu
              Tabla KM con km en 0; el km se calcula en el momento 3. Los ex-clientes ({nuevasEx.length}) no se importan
              salvo que lo pidas:
            </p>
            {nuevasEx.length > 0 && (
              <label className="mt-1 flex items-center gap-2 text-foreground">
                <input type="checkbox" checked={incluirEx} onChange={(e) => setIncluirEx(e.target.checked)} />
                Incluir también {plural(nuevasEx.length, "ex-cliente", "ex-clientes")} (sin liquidaciones en 24 meses)
              </label>
            )}
            {aImportar.length > 0 && (
              <div className="mt-2">
                <p className="mb-1 font-semibold text-foreground">Sucursales que se van a importar:</p>
                <ListaSucursales sucursales={aImportar} />
              </div>
            )}
          </VerDetalle>
        </>
      )}
      {resultado && <BrandButton onClick={irARevisar} className="self-start">Revisar pendientes →</BrandButton>}
    </div>
  );
}
