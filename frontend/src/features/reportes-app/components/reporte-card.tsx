"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  BrandBadge,
  BrandButton,
  BrandTextarea,
} from "@/shared/components/ui/brand-form";
import {
  reportesAppApi,
  type Decision,
  type EstadoReporte,
  type Reporte,
} from "../api/reportes-app-api";

export const ETIQUETA_ESTADO: Record<EstadoReporte, string> = {
  nuevo: "Nuevo",
  propuesto: "Espera tu OK",
  aprobado: "Aprobado",
  en_curso: "En curso",
  resuelto: "Resuelto",
  descartado: "Descartado",
};

const VARIANTE_ESTADO = {
  nuevo: "neutral",
  propuesto: "warning",
  aprobado: "info",
  en_curso: "info",
  resuelto: "success",
  descartado: "neutral",
} as const;

const fecha = (iso: string) =>
  new Date(iso).toLocaleString("es-AR", {
    dateStyle: "short",
    timeStyle: "short",
  });

function Bloque({ titulo, texto }: { titulo: string; texto: string }) {
  return (
    <div className="rounded-[10px] bg-muted/40 p-3">
      <p className="mb-1 font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground">
        {titulo}
      </p>
      <p className="whitespace-pre-wrap font-body text-sm text-foreground">
        {texto}
      </p>
    </div>
  );
}

function Decidir({
  reporte,
  onDecidido,
}: {
  reporte: Reporte;
  onDecidido: () => void;
}) {
  const [respuesta, setRespuesta] = useState("");
  const [enviando, setEnviando] = useState<Decision | null>(null);

  const decidir = async (decision: Decision) => {
    setEnviando(decision);
    try {
      await reportesAppApi.decidir(
        reporte.id,
        decision,
        respuesta.trim() || null,
      );
      toast.success("Decisión guardada");
      onDecidido();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "No se pudo guardar la decisión",
      );
    } finally {
      setEnviando(null);
    }
  };

  return (
    <div className="flex flex-col gap-3 border-t border-border pt-3">
      <BrandTextarea
        label="Tu comentario"
        value={respuesta}
        onChange={(e) => setRespuesta(e.target.value)}
        hint="Opcional para aprobar o descartar; obligatorio para pedir cambios."
        rows={2}
        maxLength={5000}
      />
      <div className="flex flex-wrap justify-end gap-2">
        <BrandButton
          variant="outline"
          loading={enviando === "descartar"}
          onClick={() => decidir("descartar")}
        >
          Descartar
        </BrandButton>
        <BrandButton
          variant="outline"
          loading={enviando === "pedir_cambios"}
          disabled={!respuesta.trim()}
          onClick={() => decidir("pedir_cambios")}
        >
          Pedir cambios
        </BrandButton>
        <BrandButton
          loading={enviando === "aprobar"}
          onClick={() => decidir("aprobar")}
        >
          Aprobar
        </BrandButton>
      </div>
    </div>
  );
}

export function ReporteCard({
  reporte,
  onDecidido,
}: {
  reporte: Reporte;
  onDecidido: () => void;
}) {
  return (
    <article className="flex flex-col gap-3 rounded-[12px] border border-border bg-card p-4">
      <header className="flex flex-wrap items-center gap-2">
        <BrandBadge variant={reporte.tipo === "error" ? "danger" : "accent"}>
          {reporte.tipo === "error" ? "Error" : "Mejora"}
        </BrandBadge>
        <BrandBadge variant={VARIANTE_ESTADO[reporte.estado]}>
          {ETIQUETA_ESTADO[reporte.estado]}
        </BrandBadge>
        <span className="font-body text-xs text-muted-foreground">
          {reporte.usuario ?? "Usuario eliminado"} · {fecha(reporte.creado_en)}{" "}
          · en{" "}
          <Link
            href={reporte.ruta}
            className="font-semibold text-brand-orange hover:underline"
          >
            {reporte.ruta}
          </Link>
        </span>
      </header>
      <div className="flex flex-col gap-3 md:flex-row">
        <div className="flex flex-1 flex-col gap-3">
          <Bloque titulo="Lo que se envió" texto={reporte.detalle} />
          {reporte.nota && (
            <Bloque
              titulo="Análisis y propuesta de Claude"
              texto={reporte.nota}
            />
          )}
          {reporte.respuesta && (
            <Bloque titulo="Tu comentario" texto={reporte.respuesta} />
          )}
        </div>
        {reporte.tiene_foto && (
          <a
            href={reportesAppApi.fotoUrl(reporte.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="md:w-72"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- imagen servida por la API con cookie, next/image no aporta */}
            <img
              src={reportesAppApi.fotoUrl(reporte.id)}
              alt="Captura adjunta al reporte"
              className="max-h-64 w-full rounded-[10px] border border-border object-contain"
            />
          </a>
        )}
      </div>
      {reporte.estado === "propuesto" && (
        <Decidir reporte={reporte} onDecidido={onDecidido} />
      )}
    </article>
  );
}
