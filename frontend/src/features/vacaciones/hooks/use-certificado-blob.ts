"use client";

import { useEffect, useState } from "react";

/** Trae el certificado autenticado como blob (el `<img>`/`<iframe>` no manda
 * cookies por sí solos) y expone un object URL, revocado al cambiar de `url` o
 * desmontar. `contentType` es el real de la respuesta, no la extensión. */
export function useCertificadoBlob(url: string) {
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

  return { blobUrl, contentType, error };
}
