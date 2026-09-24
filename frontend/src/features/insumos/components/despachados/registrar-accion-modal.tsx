"use client";

import { useEffect, useId, useState, type FormEvent } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandTextarea } from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { useSession } from "@/services/session-provider";
import type { NuevaAccionDespacho, ResultadoAccion, TipoAccion } from "../../types/despachados";
import { RESULTADOS, TIPOS_ACCION } from "./semaforo";

/** Guía sobre la que se registra (sale de una fila o del panel). */
export interface ObjetivoAccion {
  guia: string;
  cliente: string;
  alertaAbierta: boolean;
}

interface Props {
  objetivo: ObjetivoAccion | null;
  onClose: () => void;
  /** Hace el POST; si tira, el mensaje va al banner del modal. */
  onGuardar: (guia: string, body: NuevaAccionDespacho) => Promise<void>;
}

const LEGEND = "mb-1.5 font-body text-[11px] font-bold uppercase leading-[1.4] tracking-[.025em] text-muted-foreground";
const DETALLE_MAX = 2000;

/** Modal "Registrar acción" (~520px). El usuario y la fecha los completa el
 * backend. El formulario se desmonta al cerrar (`key` en la vista), así cada
 * apertura arranca limpia. */
export function RegistrarAccionModal({ objetivo, onClose, onGuardar }: Props) {
  if (!objetivo) return null;
  return <Formulario key={objetivo.guia} objetivo={objetivo} onClose={onClose} onGuardar={onGuardar} />;
}

function Formulario({ objetivo, onClose, onGuardar }: Props & { objetivo: ObjetivoAccion }) {
  const id = useId();
  const { user } = useSession();
  const [tipo, setTipo] = useState<TipoAccion | null>(null);
  const [detalle, setDetalle] = useState("");
  const [resultado, setResultado] = useState<ResultadoAccion>("pendiente");
  const [cerrarAlerta, setCerrarAlerta] = useState(false);
  const [intentado, setIntentado] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // El formulario se desmonta al cerrar, y `BrandModal` solo devuelve el foco
  // cuando `isOpen` pasa a false estando montado: se devuelve acá.
  useEffect(() => {
    const previo = document.activeElement as HTMLElement | null;
    return () => {
      if (previo?.isConnected) previo.focus();
    };
  }, []);

  const errorTipo = intentado && !tipo ? "Elegí el tipo de acción." : null;
  const errorDetalle = intentado && !detalle.trim() ? "Contá brevemente qué se hizo." : null;

  const submit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIntentado(true);
    if (!tipo) return document.getElementById(`${id}-tipo-0`)?.focus();
    if (!detalle.trim()) return document.getElementById(`${id}-detalle`)?.focus();
    setGuardando(true);
    setError(null);
    try {
      await onGuardar(objetivo.guia, { tipo, detalle: detalle.trim(), resultado, cerrarAlerta });
    } catch (err) {
      setError(err instanceof Error && err.message ? err.message : "No se pudo registrar la acción");
    } finally {
      setGuardando(false);
    }
  };

  return (
    <BrandModal isOpen onClose={onClose} title="Registrar acción" widthPx={520} error={error}>
      <form onSubmit={submit} noValidate className="flex flex-col gap-[18px]">
        <p className="-mt-3 font-body text-[13px] text-muted-foreground">
          Guía <span className="tabular-nums">{objetivo.guia}</span> · {objetivo.cliente}
        </p>
        <fieldset className="m-0 min-w-0 border-0 p-0">
          <legend className={LEGEND}>Tipo de acción</legend>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {TIPOS_ACCION.map((t, i) => {
              const Icon = t.icon;
              return (
                <label key={t.value} className="relative">
                  <input
                    id={`${id}-tipo-${i}`}
                    type="radio"
                    name={`${id}-tipo`}
                    value={t.value}
                    checked={tipo === t.value}
                    onChange={() => setTipo(t.value)}
                    aria-describedby={errorTipo ? `${id}-err-tipo` : undefined}
                    className="peer absolute inset-0 m-0 cursor-pointer opacity-0"
                  />
                  <span className="flex items-center gap-2 rounded-[8px] border border-border px-3 py-2.5 font-body text-[13px] font-semibold text-foreground peer-checked:border-brand-orange peer-checked:bg-brand-orange/10 peer-checked:text-[#b45f06] peer-focus-visible:ring-2 peer-focus-visible:ring-brand-orange/45 dark:peer-checked:text-brand-orange">
                    <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                    {t.label}
                  </span>
                </label>
              );
            })}
          </div>
          {errorTipo && (
            <p id={`${id}-err-tipo`} className="mt-1 font-body text-xs font-semibold text-destructive">{errorTipo}</p>
          )}
        </fieldset>

        <BrandTextarea
          id={`${id}-detalle`}
          label="Detalle"
          placeholder="Qué se hizo y qué respondió el cliente u OCA"
          value={detalle}
          maxLength={DETALLE_MAX}
          onChange={(e) => setDetalle(e.target.value)}
          error={errorDetalle}
        />

        <div>
          <p aria-hidden="true" className={LEGEND}>Resultado</p>
          <SegmentedControl
            label="Resultado"
            options={RESULTADOS}
            value={resultado}
            onChange={(v) => setResultado(v as ResultadoAccion)}
          />
        </div>

        {objetivo.alertaAbierta && (
          <label className="flex items-start gap-2.5 font-body text-[13px] text-foreground">
            <input
              type="checkbox"
              checked={cerrarAlerta}
              onChange={(e) => setCerrarAlerta(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-[#F7941D]"
            />
            <span>
              Cerrar la alerta al guardar esta acción
              <span className="block text-xs text-muted-foreground">
                El envío sale de &quot;Requieren acción&quot;. Si OCA informa otro problema, se vuelve a abrir.
              </span>
            </span>
          </label>
        )}

        <p className="flex flex-wrap gap-x-[18px] gap-y-1.5 rounded-[8px] bg-surface-2 px-3 py-2.5 font-body text-xs text-muted-foreground">
          <span>
            Registra <b className="font-semibold text-foreground">{user.fullName}</b>
          </span>
          <span>La fecha y la hora se completan solas al guardar</span>
        </p>

        <div className="flex justify-end gap-2.5 pt-1">
          <BrandButton type="button" variant="outline" onClick={onClose}>Cancelar</BrandButton>
          <BrandButton type="submit" loading={guardando}>Guardar acción</BrandButton>
        </div>
      </form>
    </BrandModal>
  );
}
