"use client";

import { useState } from "react";
import { toast } from "sonner";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { PinRoto, PinesVerificar } from "../lib/asistente-km-bandeja";
import { plural, traducirCodigoTier0, traducirPrecisionGoogle } from "../lib/asistente-km-textos";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";
import { EnlaceMaps, FilaBandeja } from "./tabla-km-wizard-ui";

function etiquetaDe(pin: PinRoto): { texto: string; destacada: boolean } {
  const fuentes = new Set(pin.evidencias.map((e) => e.fuente));
  if (pin.pinGoogle) return { texto: `${pin.pinGoogle.discrepanciaKm.toFixed(0)} km de diferencia`, destacada: true };
  if (fuentes.has("geometria")) return { texto: "pin imposible", destacada: true };
  if (fuentes.has("dos_fuentes")) return { texto: "pin en otra provincia", destacada: true };
  return { texto: "pin dudoso", destacada: false };
}

function BotonUsarDireccion({ pin, prestadorId, onCorregido }: { pin: PinRoto; prestadorId: string; onCorregido: () => Promise<void> }) {
  const [corrigiendo, setCorrigiendo] = useState(false);
  const corregir = async () => {
    setCorrigiendo(true);
    try {
      await liquidacionesApi.corregirPin(prestadorId, pin.sigesSucursalId);
      toast.success(`${pin.sucursalNombre}: ahora usa la dirección escrita`);
      await onCorregido();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "No se pudo corregir el pin");
    } finally { setCorrigiendo(false); }
  };
  return (
    <BrandButton size="sm" loading={corrigiendo} onClick={corregir}>Usar la dirección escrita</BrandButton>
  );
}

/** Un pin que ya se sabe roto (o dudoso) — una fila por sucursal, con todas sus evidencias. */
export function ItemPinRoto({ pin, prestadorId, onCambio }: { pin: PinRoto; prestadorId: string; onCambio: () => Promise<void> }) {
  const etiqueta = etiquetaDe(pin);
  const g = pin.pinGoogle;
  return (
    <FilaBandeja
      titulo={`${pin.empresaNombre} — ${pin.sucursalNombre}`}
      etiqueta={etiqueta.texto}
      etiquetaVariant={etiqueta.destacada ? "danger" : "warning"}
      destacada={etiqueta.destacada}
      acciones={
        <>
          {g ? (
            <>
              <EnlaceMaps latitud={g.latitudSiges} longitud={g.longitudSiges}>Ver pin de Gestión</EnlaceMaps>
              <EnlaceMaps latitud={g.latitudGeocode} longitud={g.longitudGeocode}>Ver dirección escrita</EnlaceMaps>
              <BotonUsarDireccion pin={pin} prestadorId={prestadorId} onCorregido={onCambio} />
            </>
          ) : (
            <EnlaceMaps latitud={pin.latitud} longitud={pin.longitud}>Ver en el mapa</EnlaceMaps>
          )}
          {pin.vaAlCsv && <span className="font-body text-xs text-muted-foreground">Va al CSV para Gestión</span>}
        </>
      }
      detalle={
        <ul className="flex flex-col gap-0.5">
          {pin.evidencias.map((e) => <li key={e.detalle}>{e.detalle}</li>)}
          {g && <li>Precisión del geocode: {traducirPrecisionGoogle(g.locationType)} · {g.formattedAddress}</li>}
          {pin.latitud !== null && <li>Coordenadas en Gestión: {pin.latitud}, {pin.longitud}</li>}
        </ul>
      }
    >
      {pin.domicilio && <p className="text-xs">Dirección: {pin.domicilio}</p>}
      <ul className="flex flex-col gap-0.5">
        {pin.evidencias.map((e) => <li key={e.texto}>{e.texto}</li>)}
      </ul>
    </FilaBandeja>
  );
}

/** Pines que comparten ubicación o están lejos de la base y que lo gratis no pudo
 * confirmar: acción en bloque, con costo visible antes (Google, solo el residuo). */
export function ItemPinesVerificar({ item, prestadorId, tope, onCambio }: {
  item: PinesVerificar; prestadorId: string; tope: number; onCambio: () => Promise<void>;
}) {
  const [auditando, setAuditando] = useState(false);
  const verificar = async () => {
    setAuditando(true);
    try {
      await liquidacionesApi.auditarPines(prestadorId, item.items.map((i) => i.sigesSucursalId));
      await onCambio();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "No se pudo verificar con Google");
    } finally { setAuditando(false); }
  };
  const n = item.items.length;
  return (
    <FilaBandeja
      titulo={`${plural(n, "sucursal comparte", "sucursales comparten")} pin con otras o ${n === 1 ? "está" : "están"} muy lejos de la base`}
      etiqueta="a verificar"
      etiquetaVariant="warning"
      acciones={
        <BotonConsumoGoogle size="sm" variant="outline" estimacion={item.estimacionGoogle} tope={tope} loading={auditando} onEjecutar={verificar}>
          Verificar {n === 1 ? "esta sucursal" : `estas ${n}`} con Google
        </BotonConsumoGoogle>
      }
      detalle={
        <ul className="max-h-[20vh] overflow-y-auto flex flex-col gap-0.5">
          {item.items.map((i) => (
            <li key={i.sigesSucursalId}>
              {i.empresaNombre} — {i.sucursalNombre}: {i.motivos.map(traducirCodigoTier0).join("; ")}
            </li>
          ))}
        </ul>
      }
    >
      No se puede confirmar gratis si el pin está bien. Verificarlas compara el pin de Gestión con la dirección
      escrita; las que difieran aparecen acá con la opción de usar la dirección escrita.
    </FilaBandeja>
  );
}
