"use client";

import { Loader2, X } from "lucide-react";
import { useState } from "react";
import { analisisLogHpApi } from "../api/analisis-log-hp-api";

interface Props {
  modelName: string;
  onClose: () => void;
  onUploaded: (url: string) => void;
}

export function CpmdUploadModal({ modelName, onClose, onUploaded }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [keywords, setKeywords] = useState(modelName);
  const [label, setLabel] = useState(modelName);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    if (!file || !keywords.trim() || !label.trim()) return;
    setUploading(true);
    setError(null);
    try {
      const { id } = await analisisLogHpApi.uploadCpmdManual(file, keywords.trim(), label.trim());
      onUploaded(`/api/analisis-log-hp/cpmd/${id}/file`);
    } catch {
      setError("No se pudo subir el manual.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-md rounded-[12px] border border-border bg-card p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="font-heading text-[16px] font-bold text-foreground">
            Subir Manual CPMD
          </h2>
          <button type="button" onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-4 w-4" />
          </button>
        </div>
        <p className="font-body text-[12px] text-muted-foreground">
          No hay un manual cargado para <strong>{modelName}</strong>. Subí el PDF de servicio.
        </p>

        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="font-body text-[12px] text-foreground"
        />

        <label className="flex flex-col gap-1">
          <span className="font-body text-[11px] font-semibold text-muted-foreground">
            Palabras clave (separadas por coma)
          </span>
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="rounded-[8px] border border-border bg-background px-3 py-2 font-body text-[13px] text-foreground"
          />
        </label>

        <label className="flex flex-col gap-1">
          <span className="font-body text-[11px] font-semibold text-muted-foreground">Nombre</span>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="rounded-[8px] border border-border bg-background px-3 py-2 font-body text-[13px] text-foreground"
          />
        </label>

        {error && <p className="font-body text-[12px] text-destructive">{error}</p>}

        <button
          type="button"
          onClick={handleUpload}
          disabled={uploading || !file || !keywords.trim() || !label.trim()}
          className="flex items-center justify-center gap-2 rounded-[8px] bg-brand-orange px-4 py-2.5 font-body text-[13px] font-bold text-white disabled:opacity-50 transition-colors"
        >
          {uploading && <Loader2 className="h-4 w-4 animate-spin" />}
          Subir manual
        </button>
      </div>
    </div>
  );
}
