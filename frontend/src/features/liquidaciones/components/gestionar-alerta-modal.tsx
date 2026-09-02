"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/shared/components/ui/badge";
import { BrandButton } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { CODIGO_ALT009, ESTADO_ALERTA_STYLES, TRANSICIONES_ALERTA } from "../lib/alerta-estados";
import type { Alerta, EstadoAlerta, PrestadorLiquidacion } from "../types/liquidaciones";
import { riesgoClass } from "./incidente-badges";
import { EntradaModal, type PlantillaEntrada } from "./tabla-km-modales";

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
  alerta,
  onClose,
  onChanged,
}: {
  liquidacionId: string;
  prestadorId: string;
  prestadores: PrestadorLiquidacion[];
  alerta: Alerta;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [enviando, setEnviando] = useState(false);
  const [transicion, setTransicion] = useState<{ estado: EstadoAlerta; label: string; pideJustificacion?: boolean } | null>(null);
  const [justificacion, setJustificacion] = useState("");
  const [cargandoSucursal, setCargandoSucursal] = useState(false);
  const estilo = ESTADO_ALERTA_STYLES[alerta.estado] ?? ESTADO_ALERTA_STYLES.pendiente;

  const cambiar = async (estado: EstadoAlerta, justificacionTexto?: string) => {
    setEnviando(true);
    try {
      await liquidacionesApi.updateEstadoAlerta(liquidacionId, alerta.id, {
        estado,
        ...(justificacionTexto ? { justificacion: justificacionTexto } : {}),
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
            {Math.round(alerta.riesgo * 100)}% riesgo
          </span>
        </div>
        {alerta.descripcion && (
          <p className="font-body text-sm text-foreground">{alerta.descripcion}</p>
        )}
        {alerta.justificacion && (
          <p className="font-body text-xs italic text-muted-foreground">
            Motivo: {alerta.justificacion}
          </p>
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
