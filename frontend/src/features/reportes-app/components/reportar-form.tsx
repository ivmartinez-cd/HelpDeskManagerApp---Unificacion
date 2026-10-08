"use client";

import { useState, type ClipboardEvent, type FormEvent } from "react";
import { toast } from "sonner";
import {
  BrandButton,
  BrandFileInput,
  BrandTextarea,
} from "@/shared/components/ui/brand-form";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { reportesAppApi, type TipoReporte } from "../api/reportes-app-api";

const TIPOS = [
  { value: "error", label: "Error" },
  { value: "mejora", label: "Mejora" },
];

/** Una captura pegada con Ctrl+V llega como archivo del portapapeles. */
function imagenPegada(e: ClipboardEvent): File | null {
  const item = Array.from(e.clipboardData.items).find((i) =>
    i.type.startsWith("image/"),
  );
  return item?.getAsFile() ?? null;
}

export function ReportarForm({ onEnviado }: { onEnviado: () => void }) {
  const [tipo, setTipo] = useState<TipoReporte>("error");
  const [detalle, setDetalle] = useState("");
  const [foto, setFoto] = useState<File | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onPaste = (e: ClipboardEvent) => {
    const pegada = imagenPegada(e);
    if (pegada) setFoto(pegada);
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const ruta = window.location.pathname + window.location.search;
      await reportesAppApi.crear({ tipo, detalle: detalle.trim(), ruta, foto });
      toast.success("Reporte enviado. ¡Gracias!");
      onEnviado();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No se pudo enviar el reporte",
      );
    } finally {
      setEnviando(false);
    }
  };

  return (
    <form onSubmit={onSubmit} onPaste={onPaste} className="flex flex-col gap-4">
      <SegmentedControl
        label="Tipo de reporte"
        options={TIPOS}
        value={tipo}
        onChange={(v) => setTipo(v as TipoReporte)}
      />
      <BrandTextarea
        label="Detalle"
        value={detalle}
        onChange={(e) => setDetalle(e.target.value)}
        placeholder={
          tipo === "error"
            ? "Qué hiciste, qué esperabas y qué pasó"
            : "Qué te gustaría que haga"
        }
        hint="Podés pegar una captura de pantalla con Ctrl+V."
        required
        minLength={5}
        maxLength={5000}
        rows={5}
      />
      <BrandFileInput
        label="Foto (opcional)"
        accept="image/png,image/jpeg,image/webp"
        onChange={(e) => setFoto(e.target.files?.[0] ?? null)}
        hint={foto ? `Adjunta: ${foto.name || "captura pegada"}` : undefined}
      />
      {error && (
        <p className="font-body text-xs font-semibold text-destructive">
          {error}
        </p>
      )}
      <div className="flex justify-end">
        <BrandButton
          type="submit"
          loading={enviando}
          disabled={detalle.trim().length < 5}
        >
          Enviar
        </BrandButton>
      </div>
    </form>
  );
}
