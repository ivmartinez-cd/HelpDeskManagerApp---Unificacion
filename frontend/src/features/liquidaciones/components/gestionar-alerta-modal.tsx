"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { CODIGO_ALT009, ESTADO_ALERTA_STYLES, TRANSICIONES_ALERTA } from "../lib/alerta-estados";
import { formatARS } from "../lib/format";
import type { Alerta, EstadoAlerta, Incidente, PrestadorLiquidacion } from "../types/liquidaciones";
import { riesgoClass } from "./incidente-badges";
import { AlertaKmAcciones } from "./alerta-km-acciones";
import { AsignarZonaSucursal } from "./asignar-zona-sucursal";
import { EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";

const CODIGO_ALT001 = "ALT001";
const CODIGO_ALT002 = "ALT002";
const CODIGO_ALT008 = "ALT008";

function plantillaDesdeAlerta(alerta: Alerta): PlantillaEntrada {
  const ctx = alerta.datosContexto as { empresa?: string; sucursal?: string } | null;
  return {
    empresaNombre: ctx?.empresa ?? "",
    sucursalNombre: ctx?.sucursal ?? "",
    domicilioCliente: "",
    localidadCliente: "",
    provinciaCliente: "",
  };
}

/** Modal de gestión de una alerta individual, abierto desde el "Gestionar"
 * de `AlertaSubRow`. Reemplaza a la sección "Alertas" standalone: las
 * mismas transiciones (`TRANSICIONES_ALERTA`) ahora se resuelven acá en
 * vez de en una fila de tabla aparte. */
export function GestionarAlertaModal({
  liquidacionId,
  prestadorId,
  prestadores,
  incidentesById,
  alerta,
  onClose,
  onChanged,
}: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  incidentesById: Record<string, Incidente>;
  alerta: Alerta;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [enviando, setEnviando] = useState(false);
  const [transicion, setTransicion] = useState<{ estado: EstadoAlerta; label: string; pideJustificacion?: boolean } | null>(null);
  const [justificacion, setJustificacion] = useState("");
  const [incidenteRelacionadoId, setIncidenteRelacionadoId] = useState(
    alerta.incidenteRelacionadoId ?? "",
  );
  const [cargandoSucursal, setCargandoSucursal] = useState(false);
  const estilo = ESTADO_ALERTA_STYLES[alerta.estado] ?? ESTADO_ALERTA_STYLES.pendiente;
  // El selector de "ruta compartida" es un vínculo MANUAL para una alerta 1:1
  // (ver Alerta.incidenteRelacionadoId) — una alerta ya agrupada por el motor
  // (esGrupo) no lo necesita, el grupo ya está resuelto.
  const candidatosRuta = alerta.esGrupo
    ? []
    : Object.values(incidentesById)
        .filter((i) => i.id !== alerta.incidenteId)
        .sort((a, b) => a.numeroIncidente.localeCompare(b.numeroIncidente));
  // ALT008 con `spst_id` null en el contexto = la fila de Tabla KM de la
  // sucursal no tiene zona (ver `linkFaltante` en alerta-sub-row.tsx): se
  // resuelve acá, sin ir a Tabla KM.
  const incidente = incidentesById[alerta.incidenteId];
  const ctxAlt008 = alerta.datosContexto as { spst_id?: string | null } | null;
  const sinZona =
    alerta.tipoAlerta === CODIGO_ALT008 &&
    !ctxAlt008?.spst_id &&
    !!incidente?.empresaNombre &&
    !!incidente?.sucursalNombre &&
    (alerta.estado === "pendiente" || alerta.estado === "en_revision");
  // ALT001 pendiente: atajo para dejar asentado el arreglo con ese cliente una
  // sola vez (acuerdo de precio) en vez de resolver la misma alerta cada mes.
  const ctxAlt001 = alerta.datosContexto as { cobrado?: number } | null;
  const linkAcuerdo =
    alerta.tipoAlerta === CODIGO_ALT001 &&
    !!incidente?.empresaNombre &&
    (alerta.estado === "pendiente" || alerta.estado === "en_revision")
      ? `/liquidaciones/configuracion/acuerdos?${new URLSearchParams({
          prestadorId,
          empresa: incidente.empresaNombre,
          tipo: incidente.tipo,
          cobrado: String(ctxAlt001?.cobrado ?? ""),
        })}`
      : null;
  const incidentesMismaSucursal = incidente
    ? Object.values(incidentesById).filter(
        (i) => i.empresaNombre === incidente.empresaNombre && i.sucursalNombre === incidente.sucursalNombre,
      ).length
    : 0;

  const cambiar = async (estado: EstadoAlerta, justificacionTexto?: string) => {
    setEnviando(true);
    try {
      await liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, {
        estado,
        ...(justificacionTexto ? { justificacion: justificacionTexto } : {}),
        incidenteRelacionadoId: incidenteRelacionadoId || null,
      });
      onChanged();
      onClose();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Error al cambiar el estado de la alerta");
    } finally {
      setEnviando(false);
    }
  };

  if (cargandoSucursal) {
    return (
      <EntradaModal
        isOpen
        onClose={onClose}
        prestadores={prestadores}
        editing={null}
        defaultPrestadorId={prestadorId}
        plantilla={plantillaDesdeAlerta(alerta)}
        title="Cargar sucursal en Tabla KM"
        onSuccess={() => void cambiar("resuelta")}
      />
    );
  }

  return (
    <BrandModal isOpen onClose={onClose} title={`Gestionar ${alerta.tipoAlerta}`} widthPx={460}>
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <Badge variant={estilo.variant}>{estilo.label}</Badge>
          <span className={`font-body text-sm font-semibold tabular-nums ${riesgoClass(alerta.riesgo)}`}>
            {Math.round(alerta.riesgo)}% riesgo
          </span>
          {alerta.esGrupo && (
            <span className="rounded-full bg-muted px-1.5 py-0.5 font-body text-[10px] font-bold uppercase text-muted-foreground">
              Grupo ({alerta.grupoIncidenteIds.length} incidentes)
            </span>
          )}
        </div>
        {alerta.descripcion && (
          <p className="font-body text-sm text-foreground">{alerta.descripcion}</p>
        )}
        {alerta.esGrupo && alerta.diferencia !== null && (
          <p className="font-body text-xs text-muted-foreground">
            Cobrado {formatARS(alerta.montoCobrado ?? 0)} · Esperado{" "}
            {formatARS(alerta.montoEsperado ?? 0)} · Diferencia{" "}
            {formatARS(alerta.diferencia)}
          </p>
        )}
        {alerta.justificacion && (
          <p className="font-body text-xs italic text-muted-foreground">
            Motivo: {alerta.justificacion}
          </p>
        )}
        {linkAcuerdo && !transicion && (
          <p className="font-body text-xs text-muted-foreground">
            ¿Es un arreglo con este cliente que se repite todos los meses?{" "}
            <Link href={linkAcuerdo} className="font-semibold text-brand-orange hover:underline">
              Cargar acuerdo de precio para {incidente?.empresaNombre} →
            </Link>
          </p>
        )}
        {alerta.tipoAlerta === CODIGO_ALT002 &&
          incidente &&
          !transicion &&
          (alerta.estado === "pendiente" || alerta.estado === "en_revision") && (
            <AlertaKmAcciones
              liquidacionId={liquidacionId}
              prestadorId={prestadorId}
              alerta={alerta}
              incidente={incidente}
              onChanged={onChanged}
              onClose={onClose}
            />
          )}
        {sinZona && incidente && !transicion && (
          <AsignarZonaSucursal
            prestadorId={prestadorId}
            empresaNombre={incidente.empresaNombre!}
            sucursalNombre={incidente.sucursalNombre!}
            incidentesAfectados={incidentesMismaSucursal}
            onAsignada={() => {
              onChanged();
              onClose();
            }}
          />
        )}

        {transicion ? (
          <>
            <textarea
              value={justificacion}
              onChange={(e) => setJustificacion(e.target.value)}
              rows={3}
              placeholder={
                transicion.pideJustificacion
                  ? "Ej.: diferencia acordada con el prestador"
                  : "Nota (opcional)"
              }
              autoFocus
              className="w-full rounded-[8px] border border-border bg-background p-3 font-body text-sm text-foreground outline-none focus:border-brand-orange"
            />
            {candidatosRuta.length > 0 && (
              <label className="flex flex-col gap-1 font-body text-xs text-muted-foreground">
                Ruta compartida con (opcional):
                <select
                  value={incidenteRelacionadoId}
                  onChange={(e) => setIncidenteRelacionadoId(e.target.value)}
                  className="rounded-[8px] border border-border bg-background px-3 py-2 font-body text-sm text-foreground outline-none focus:border-brand-orange"
                >
                  <option value="">Ninguno</option>
                  {candidatosRuta.map((i) => (
                    <option key={i.id} value={i.id}>
                      #{i.numeroIncidente} —{" "}
                      {[i.empresaNombre, i.sucursalNombre].filter(Boolean).join(" / ") || "—"}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <div className="flex justify-end gap-2">
              <BrandButton variant="outline" onClick={() => setTransicion(null)}>
                Volver
              </BrandButton>
              <BrandButton
                loading={enviando}
                disabled={transicion.pideJustificacion && !justificacion.trim()}
                onClick={() => void cambiar(transicion.estado, justificacion.trim() || undefined)}
              >
                {transicion.label}
              </BrandButton>
            </div>
          </>
        ) : (
          <div className="flex justify-end gap-2">
            <BrandButton variant="outline" onClick={onClose}>
              Cerrar
            </BrandButton>
            {(TRANSICIONES_ALERTA[alerta.estado] ?? []).map((t) => (
              <BrandButton
                key={t.estado}
                loading={enviando}
                onClick={() => {
                  // Para ALT009 tanto "Revisar" como "Resolver" llevan al mismo lugar: no
                  // hay nada que revisar sin antes cargar la sucursal faltante en Tabla KM.
                  const abreCargaSucursal =
                    alerta.tipoAlerta === CODIGO_ALT009 &&
                    !t.pideJustificacion &&
                    (alerta.estado === "pendiente" || alerta.estado === "en_revision");
                  if (abreCargaSucursal) setCargandoSucursal(true);
                  else {
                    setJustificacion("");
                    setTransicion(t);
                  }
                }}
              >
                {t.label}
              </BrandButton>
            ))}
          </div>
        )}
      </div>
    </BrandModal>
  );
}
