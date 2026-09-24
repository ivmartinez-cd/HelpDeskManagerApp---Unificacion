"use client";

import { useEffect, useRef, useState } from "react";
import { AlertTriangle, Copy, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { BrandButton, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { copiarTexto } from "@/shared/utils/clipboard";
import { despachadosApi } from "../../api/despachados-api";
import { mensajeDeError } from "../../hooks/use-despachados-listado";
import type { ReclamoOca } from "../../types/despachados";
import { esperarFormularioOca, montarFormularioOca, OCA_FORM, valoresFormulario } from "./oca-reclamo-form";

interface Props {
  guia: string | null;
  /** Recibe el reclamo si llegó a cargarse (para ofrecer registrar la acción). */
  onClose: (reclamo: ReclamoOca | null) => void;
}

type Estado = "cargando" | "formulario" | "listo" | "respaldo";

/** Modal "Reclamar en OCA" (~720px): incrusta el formulario público de
 * reclamos de OCA y lo precarga con `GET /reclamo-oca`. HDM no envía nada: el
 * operador revisa, adjunta, pasa la verificación y envía él mismo. Si el
 * formulario no carga, queda el link a la página de OCA y el comentario para
 * copiar. Se desmonta al cerrar (`key` por guía), así cada apertura arranca
 * limpia. */
export function ReclamarOcaModal({ guia, onClose }: Props) {
  if (!guia) return null;
  return <Contenido key={guia} guia={guia} onClose={onClose} />;
}

function Contenido({ guia, onClose }: { guia: string; onClose: Props["onClose"] }) {
  const [reclamo, setReclamo] = useState<ReclamoOca | null>(null);
  const [estado, setEstado] = useState<Estado>("cargando");
  const [error, setError] = useState<string | null>(null);
  const contenedor = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let vigente = true;
    despachadosApi.getReclamoOca(guia).then(
      (r) => {
        if (!vigente) return;
        setReclamo(r);
        setEstado("formulario");
      },
      (err) => {
        if (!vigente) return;
        setError(mensajeDeError(err, "No se pudieron preparar los datos del reclamo"));
        setEstado("respaldo");
      },
    );
    return () => {
      vigente = false;
    };
  }, [guia]);

  useEffect(() => {
    const nodo = contenedor.current;
    if (!reclamo || !nodo) return;
    const espera = esperarFormularioOca();
    let limpiar = () => {};
    // Diferido: en dev, StrictMode monta, limpia y vuelve a montar al instante;
    // así el primer montaje no llega a inyectar el loader de Bitrix24.
    const timer = window.setTimeout(() => {
      limpiar = montarFormularioOca(nodo, () => setEstado("respaldo"));
    });
    espera.promesa
      .then((form) => {
        form.setValues(valoresFormulario(reclamo, form));
        setEstado("listo");
      })
      .catch(() => setEstado("respaldo"));
    return () => {
      window.clearTimeout(timer);
      espera.cancelar();
      limpiar();
    };
  }, [reclamo]);

  return (
    <BrandModal isOpen onClose={() => onClose(reclamo)} title="Reclamar en OCA" widthPx={720} error={error}>
      <p className="-mt-3 mb-3 font-body text-[13px] text-muted-foreground">
        Guía <span className="tabular-nums">{guia}</span> · Formulario de grandes cuentas de OCA, precargado.
        Revisalo, adjuntá lo que haga falta y envialo desde acá: HDM no lo envía.
      </p>
      {estado === "respaldo" && <Respaldo reclamo={reclamo} />}
      {estado === "cargando" && <BrandSkeleton className="h-64 w-full" />}
      {estado === "formulario" && (
        <p role="status" className="mb-2 font-body text-xs text-muted-foreground">Cargando el formulario de OCA…</p>
      )}
      {reclamo && !reclamo.contacto && estado === "listo" && (
        <p className="mb-2 font-body text-xs text-muted-foreground">
          Esta guía no corresponde a ninguna cuenta configurada: completá los datos de contacto a mano.
        </p>
      )}
      <div ref={contenedor} data-testid="oca-formulario" hidden={estado === "respaldo"} />
    </BrandModal>
  );
}

function Respaldo({ reclamo }: { reclamo: ReclamoOca | null }) {
  const copiar = async () => {
    if (!reclamo) return;
    try {
      await copiarTexto(reclamo.comentario);
      toast.success("Comentario copiado");
    } catch {
      toast.error("No se pudo copiar. Seleccioná el texto a mano.");
    }
  };
  return (
    <div role="alert" className="flex flex-col gap-3 rounded-[10px] border border-[rgba(247,148,29,.35)] bg-[rgba(247,148,29,.08)] p-3.5 font-body text-[13px] text-foreground">
      <p className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 flex-none text-[#b45f06] dark:text-brand-orange" aria-hidden="true" />
        No se pudo cargar el formulario de OCA acá. Abrilo en su página y pegá los datos.
      </p>
      <a
        href={OCA_FORM.paginaPublica}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 self-start font-bold text-[#b45f06] no-underline hover:underline dark:text-brand-orange"
      >
        <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        Abrir el formulario de OCA
      </a>
      {reclamo && (
        <>
          <pre data-testid="oca-comentario" className="m-0 whitespace-pre-wrap rounded-[8px] bg-surface-2 p-3 font-body text-xs select-all">
            {reclamo.comentario}
          </pre>
          <BrandButton type="button" variant="outline" size="sm" className="self-start rounded-[8px]" onClick={() => void copiar()}>
            <Copy className="h-3.5 w-3.5" aria-hidden="true" />
            Copiar comentario
          </BrandButton>
        </>
      )}
    </div>
  );
}
