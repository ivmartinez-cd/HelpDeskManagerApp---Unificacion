"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "../api/liquidaciones-api";
import type { ItemWorklistTier2, PinSospechoso, ResultadoWorklistTier2 } from "../types/liquidaciones";
import { BotonConsumoGoogle } from "./tabla-km-wizard-confirmar-google";
import { Tarjeta } from "./tabla-km-wizard-pines-tier0";

function EnlaceMaps({ latitud, longitud, texto }: {
  latitud: number | null; longitud: number | null; texto: string;
}) {
  if (latitud === null || longitud === null) return null;
  return (
    <a
      href={`https://www.google.com/maps?q=${latitud},${longitud}`}
      target="_blank"
      rel="noopener noreferrer"
      className="font-body text-[11px] font-bold uppercase tracking-wide text-brand-orange hover:underline"
    >
      {texto}
    </a>
  );
}

function ItemCertezaAbsoluta({ item }: { item: ItemWorklistTier2 }) {
  return (
    <div className="rounded-[8px] border border-destructive/40 bg-destructive/5 px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground truncate">
          {item.empresaNombre} — {item.sucursalNombre}
        </p>
        <Badge variant="danger">corregir en Gestión</Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">
        {item.domicilio ?? "sin domicilio"} · {item.motivos.join(", ")}
      </p>
      <EnlaceMaps latitud={item.latitud} longitud={item.longitud} texto="Ver pin en Maps" />
    </div>
  );
}

function ItemPinConfirmado({ pin, prestadorId, onCorregido }: {
  pin: PinSospechoso; prestadorId: string; onCorregido: () => void;
}) {
  const [corrigiendo, setCorrigiendo] = useState(false);
  const corregir = async () => {
    setCorrigiendo(true);
    try {
      await liquidacionesApi.corregirPin(prestadorId, pin.sigesSucursalId);
      toast.success(`${pin.empresaNombre}: pin corregido`);
      onCorregido();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al corregir pin");
    } finally { setCorrigiendo(false); }
  };
  return (
    <div className="rounded-[8px] border border-border px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="font-body text-sm font-semibold text-foreground truncate">
          {pin.empresaNombre} — {pin.sucursalNombre}
        </p>
        <Badge variant={pin.locationType === "ROOFTOP" ? "danger" : "warning"}>
          {pin.discrepanciaKm.toFixed(1)} km de diferencia
        </Badge>
      </div>
      <p className="mt-0.5 font-body text-xs text-muted-foreground">{pin.direccion}</p>
      <div className="mt-2 flex items-center justify-between gap-2">
        <div className="flex gap-3">
          <EnlaceMaps latitud={pin.latitudSiges} longitud={pin.longitudSiges} texto="Ver pin de Gestión" />
          <EnlaceMaps latitud={pin.latitudGeocode} longitud={pin.longitudGeocode} texto="Ver dirección escrita" />
        </div>
        <BrandButton type="button" size="sm" variant="outline" loading={corrigiendo} onClick={corregir}>
          Usar la dirección escrita
        </BrandButton>
      </div>
    </div>
  );
}

/** Vista rankeada única que junta lo que YA se sabe con certeza que hay que
 * corregir en Gestión: los hallazgos de Tier 0 (sin ambigüedad, dominio puro)
 * primero, y después los pines que Google confirmó que difieren de la
 * dirección escrita — mismos 2 grupos que junta el CSV, antes repartidos en
 * dos pantallas separadas. */
export function SeccionWorklistFinal({ prestadorId, tope, estimacionAuditarPines, onCambio }: {
  prestadorId: string; tope: number; estimacionAuditarPines: number; onCambio: () => void;
}) {
  const [worklist, setWorklist] = useState<ResultadoWorklistTier2 | null>(null);
  const [pines, setPines] = useState<PinSospechoso[] | null>(null);
  const [auditandoResiduo, setAuditandoResiduo] = useState(false);
  const [auditandoCompleto, setAuditandoCompleto] = useState(false);
  const [exportando, setExportando] = useState(false);
  const [huboAuditoria, setHuboAuditoria] = useState(false);

  const refresh = () =>
    Promise.all([
      liquidacionesApi.getWorklistTier2(prestadorId).then(setWorklist).catch(() => setWorklist(null)),
      liquidacionesApi.listPinesSospechosos(prestadorId).then(setPines).catch(() => setPines([])),
    ]);
  useEffect(() => { void refresh(); }, [prestadorId]); // eslint-disable-line react-hooks/exhaustive-deps

  const recargar = async () => {
    await refresh();
    onCambio();
  };

  const auditarResiduo = async () => {
    if (!worklist) return;
    setAuditandoResiduo(true);
    try {
      const ids = worklist.requiereVerificacion.map((i) => i.sigesSucursalId);
      await liquidacionesApi.auditarPines(prestadorId, ids);
      setHuboAuditoria(true);
      await recargar();
    } finally { setAuditandoResiduo(false); }
  };

  const auditarCompleto = async () => {
    setAuditandoCompleto(true);
    try {
      await liquidacionesApi.auditarPines(prestadorId);
      setHuboAuditoria(true);
      await recargar();
    } finally { setAuditandoCompleto(false); }
  };

  const exportarCsv = async () => {
    setExportando(true);
    try {
      await liquidacionesApi.exportWorklistCsv(prestadorId);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Error al exportar el CSV");
    } finally { setExportando(false); }
  };

  const cargando = worklist === null || pines === null;
  const total = (worklist?.certezaAbsoluta.length ?? 0) + (pines?.length ?? 0);

  return (
    <Tarjeta
      numero="1d"
      titulo="Worklist final — a corregir en Gestión"
      descripcion="Lo que Georef y Nominatim ya confirmaron con certeza no necesita Google. Certeza absoluta (Tier 0) + pines que Google confirmó que difieren de la dirección escrita: nunca el prestador completo."
    >
      {cargando ? (
        <div className="flex h-16 items-center justify-center"><Spinner /></div>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <BrandButton size="sm" variant="outline" loading={exportando} onClick={exportarCsv}>
              Exportar CSV para Gestión
            </BrandButton>
            <BotonConsumoGoogle
              size="sm"
              variant="outline"
              estimacion={estimacionAuditarPines}
              tope={tope}
              loading={auditandoCompleto}
              onEjecutar={auditarCompleto}
            >
              Verificar todos los pines con Google
            </BotonConsumoGoogle>
          </div>

          {total > 0 ? (
            <div className="flex max-h-[40vh] flex-col gap-1.5 overflow-y-auto pr-1">
              {worklist?.certezaAbsoluta.map((i) => (
                <ItemCertezaAbsoluta key={`t0-${i.sigesSucursalId}`} item={i} />
              ))}
              {pines?.map((p) => (
                <ItemPinConfirmado
                  key={`t2-${p.sigesSucursalId}`}
                  pin={p}
                  prestadorId={prestadorId}
                  onCorregido={recargar}
                />
              ))}
            </div>
          ) : huboAuditoria ? (
            <p className="font-body text-sm text-muted-foreground italic">
              ✓ Nada pendiente de corregir. Podés finalizar.
            </p>
          ) : (
            <p className="font-body text-sm text-muted-foreground italic">
              Todavía no hay pines confirmados por Google. Auditá el residuo o el prestador
              completo para completar esta lista.
            </p>
          )}

          {worklist && worklist.requiereVerificacion.length > 0 && (
            <BotonConsumoGoogle
              size="sm"
              variant="outline"
              estimacion={worklist.estimacionLlamadasGoogle}
              tope={tope}
              loading={auditandoResiduo}
              onEjecutar={auditarResiduo}
            >
              Auditar residuo con Google ({worklist.requiereVerificacion.length} sucursales)
            </BotonConsumoGoogle>
          )}
        </div>
      )}
    </Tarjeta>
  );
}
