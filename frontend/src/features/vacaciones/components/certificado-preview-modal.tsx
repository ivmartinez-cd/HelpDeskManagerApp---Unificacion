"use client";

import { Download, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { BrandModal } from "@/shared/components/ui/brand-modal";

interface Props {
  url: string;
  onClose: () => void;
}

const EXTENSION_POR_TIPO: Record<string, string> = {
  "application/pdf": ".pdf",
  "image/jpeg": ".jpg",
  "image/png": ".png",
};

/** Previsualiza el certificado/orden médica de una `Ausencia` sin forzar la
 * descarga: trae el blob autenticado (el `<img>`/`<iframe>` no manda cookies
 * por sí solos) y lo muestra según su content-type real, no la extensión. */
export function CertificadoPreviewModal({ url, onClose }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [contentType, setContentType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    fetch(url, { credentials: "include" })
      .then((res) => {
        if (!res.ok) throw new Error("No se pudo cargar el certificado");
        setContentType(res.headers.get("content-type"));
        return res.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setError("No se pudo cargar el certificado.");
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  const extension = contentType ? (EXTENSION_POR_TIPO[contentType] ?? "") : "";

  return (
    <BrandModal isOpen onClose={onClose} title="Certificado adjunto" widthPx={640}>
      <div className="flex flex-col gap-3">
        {error && <p className="font-body text-sm text-destructive">{error}</p>}

        {!error && !blobUrl && (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        )}

        {blobUrl && contentType?.startsWith("image/") && (
          // eslint-disable-next-line @next/next/no-img-element -- blob: URL autenticado, next/image no lo sirve
          <img
            src={blobUrl}
            alt="Certificado adjunto"
            className="max-h-[70vh] w-full rounded-[8px] object-contain"
          />
        )}

        {blobUrl && contentType === "application/pdf" && (
          <iframe
            src={blobUrl}
            title="Certificado adjunto"
            className="h-[70vh] w-full rounded-[8px] border border-border"
          />
        )}

        {blobUrl && (
          <a
            href={blobUrl}
            download={`certificado${extension}`}
            className="flex items-center gap-1.5 self-end rounded-[8px] border border-border px-3 py-1.5 font-body text-xs font-semibold text-foreground hover:bg-muted"
          >
            <Download className="h-3.5 w-3.5" />
            Descargar
          </a>
        )}
      </div>
    </BrandModal>
  );
}
