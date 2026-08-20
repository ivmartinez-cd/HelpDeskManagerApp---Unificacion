"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton, BrandInput } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { SinUbicacion, UbicacionElegir, UbicacionSinResultado } from "../lib/asistente-km-bandeja";
import { plural, traducirPrecisionGoogle } from "../lib/asistente-km-textos";
import type { GeocodificarResultado, SucursalCoordenadas } from "../types/liquidaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";
import { EnlaceMaps, FilaBandeja, VerDetalle } from "./tabla-km-wizard-ui";

type ElegirBody = { candidatoIdx?: number; latitud?: number; longitud?: number };

function useElegir(prestadorId: string, fila: SucursalCoordenadas, onCambio: () => Promise<void>) {
  const [enviando, setEnviando] = useState(false);
  const elegir = async (body: ElegirBody) => {
    setEnviando(true);
    try {
      await liquidacionesApi.resolverCoordenadas(prestadorId, fila.sigesSucursalId, body);
      toast.success(`${fila.sucursalNombre}: ubicación guardada`);
      await onCambio();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "No se pudo guardar la ubicación");
    } finally { setEnviando(false); }
  };
  return { elegir, enviando };
}

function CargaManual({ enviando, onElegir }: { enviando: boolean; onElegir: (b: ElegirBody) => Promise<void> }) {
  const [lat, setLat] = useState("");
  const [lon, setLon] = useState("");
  const valida = Number.isFinite(parseFloat(lat)) && Number.isFinite(parseFloat(lon));
  return (
    <VerDetalle etiqueta="Cargar coordenadas a mano">
      <div className="flex items-end gap-2">
        <BrandInput label="Latitud" value={lat} placeholder="-31.5375" onChange={(e) => setLat(e.target.value)} />
        <BrandInput label="Longitud" value={lon} placeholder="-68.5364" onChange={(e) => setLon(e.target.value)} />
        <BrandButton size="sm" variant="outline" disabled={!valida || enviando} onClick={() => onElegir({ latitud: parseFloat(lat), longitud: parseFloat(lon) })}>
          Usar estas
        </BrandButton>
      </div>
    </VerDetalle>
  );
}

/** Google devolvió más de una opción: elegís vos (no consulta Google). */
export function ItemUbicacionElegir({ item, prestadorId, onCambio }: { item: UbicacionElegir; prestadorId: string; onCambio: () => Promise<void> }) {
  const { fila } = item;
  const { elegir, enviando } = useElegir(prestadorId, fila, onCambio);
  return (
    <FilaBandeja
      titulo={`${fila.empresaNombre} — ${fila.sucursalNombre}`}
      etiqueta="elegí la ubicación"
      etiquetaVariant="warning"
      detalle={
        <ul className="flex flex-col gap-0.5">
          {fila.candidatos.map((c, i) => (
            <li key={`${c.latitud},${c.longitud}`}>
              Opción {i + 1}: {c.latitud.toFixed(6)}, {c.longitud.toFixed(6)} · {c.locationType}{c.partialMatch ? " · match parcial" : ""}
            </li>
          ))}
        </ul>
      }
    >
      <p className="mb-2 text-xs">Dirección: {fila.direccion ?? "sin dirección escrita"}. Google encontró {plural(fila.candidatos.length, "opción", "opciones")}:</p>
      <ul className="flex flex-col gap-1.5">
        {fila.candidatos.map((c, idx) => (
          <li key={`${c.latitud},${c.longitud}`} className="flex items-center justify-between gap-3 rounded-[6px] bg-muted/30 px-3 py-2">
            <div className="min-w-0">
              <p className="truncate font-body text-[13px] text-foreground" title={c.formattedAddress}>{c.formattedAddress}</p>
              <p className="font-body text-[11px] text-muted-foreground">{traducirPrecisionGoogle(c.locationType)}{c.partialMatch ? " · coincidencia parcial" : ""}</p>
            </div>
            <div className="flex flex-shrink-0 items-center gap-2">
              <EnlaceMaps latitud={c.latitud} longitud={c.longitud}>Ver en el mapa</EnlaceMaps>
              <BrandButton size="sm" disabled={enviando} onClick={() => elegir({ candidatoIdx: idx })}>Usar</BrandButton>
            </div>
          </li>
        ))}
      </ul>
      <div className="mt-2"><CargaManual enviando={enviando} onElegir={elegir} /></div>
    </FilaBandeja>
  );
}

/** Google no encontró la dirección (o no hay dirección escrita): se resuelve a mano o en Gestión. */
export function ItemUbicacionSinResultado({ item, prestadorId, onCambio }: { item: UbicacionSinResultado; prestadorId: string; onCambio: () => Promise<void> }) {
  const { fila } = item;
  const { elegir, enviando } = useElegir(prestadorId, fila, onCambio);
  const sinDireccion = fila.estado === "sin_direccion";
  return (
    <FilaBandeja titulo={`${fila.empresaNombre} — ${fila.sucursalNombre}`} etiqueta="sin ubicación" etiquetaVariant="neutral">
      <p>
        {sinDireccion
          ? "No tiene dirección escrita en Gestión, así que no se puede buscar."
          : `Google no encontró "${fila.direccion}".`}
        {" "}Corregí la dirección en Gestión o cargá las coordenadas a mano.
      </p>
      <div className="mt-2"><CargaManual enviando={enviando} onElegir={elegir} /></div>
    </FilaBandeja>
  );
}

/** Sucursales sin ubicación: acción en bloque con costo visible antes (Google). */
export function ItemSinUbicacion({ item, prestadorId, tope, onCambio }: {
  item: SinUbicacion; prestadorId: string; tope: number; onCambio: () => Promise<void>;
}) {
  const [buscando, setBuscando] = useState(false);
  const [resumen, setResumen] = useState<GeocodificarResultado | null>(null);
  const buscar = async () => {
    setBuscando(true);
    try {
      setResumen(await liquidacionesApi.geocodificarFaltantes(prestadorId));
      await onCambio();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "No se pudieron buscar las ubicaciones");
    } finally { setBuscando(false); }
  };
  return (
    <FilaBandeja
      titulo={`${plural(item.cantidad, "sucursal no tiene", "sucursales no tienen")} ubicación`}
      etiqueta="sin ubicación"
      etiquetaVariant="warning"
      acciones={
        <BotonConsumoGoogle size="sm" variant="outline" estimacion={item.estimacionGoogle} tope={tope} loading={buscando} onEjecutar={buscar}>
          Buscar ubicaciones
        </BotonConsumoGoogle>
      }
    >
      <p>Sin ubicación no se les puede calcular km. Buscarlas usa la dirección escrita en Gestión: las inequívocas se guardan solas y las dudosas aparecen acá para que elijas.</p>
      {resumen && (
        <p className="mt-1 text-foreground">
          Resultado: {resumen.resueltasAuto} resueltas solas · {resumen.ambiguas} para elegir · {resumen.sinResultados} sin resultado ·{" "}
          {resumen.sinDireccion} sin dirección escrita · {resumen.llamadasGoogle} consultas usadas
          {resumen.pendientesPorTope > 0 && ` · ${resumen.pendientesPorTope} quedaron para otra corrida (tope)`}.
        </p>
      )}
    </FilaBandeja>
  );
}
