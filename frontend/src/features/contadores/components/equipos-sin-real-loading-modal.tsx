"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

/** Modal de carga para la primera consulta (caché fría en el backend,
 * ~10-15 s recorriendo el historial de Contadores en Siges). "Inteligente"
 * en dos sentidos: espera 400 ms antes de mostrarse (con caché tibia la
 * respuesta llega antes y no flashea), y va cambiando el mensaje según el
 * tiempo transcurrido para que la espera no parezca un cuelgue. */

// Con caché tibia la carga completa (navegación + fetch) ronda los 900 ms —
// medido con Playwright; por debajo de este umbral el modal solo flashearía.
const APARICION_MS = 1000;

function etapaPorSegundos(s: number): string {
  if (s < 5) return "Consultando el parque de equipos…";
  if (s < 12) return "Analizando el historial de tomas de contadores…";
  if (s < 20) return "Un momento más, ya casi está…";
  return "La base está lenta hoy — seguimos esperando la respuesta…";
}

export function EquiposSinRealLoadingModal() {
  const [visible, setVisible] = useState(false);
  const [segundos, setSegundos] = useState(0);

  useEffect(() => {
    const aparicion = setTimeout(() => setVisible(true), APARICION_MS);
    const reloj = setInterval(() => setSegundos((s) => s + 1), 1000);
    return () => {
      clearTimeout(aparicion);
      clearInterval(reloj);
    };
  }, []);

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Consultando Siges"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-[2px]"
    >
      <div className="flex w-[440px] max-w-[calc(100vw-2rem)] flex-col items-center gap-3 rounded-[16px] border border-border bg-card px-8 py-9 text-center shadow-2xl">
        <Loader2 className="h-9 w-9 animate-spin text-brand-orange" aria-hidden="true" />
        <h2 className="font-heading text-lg font-extrabold uppercase tracking-[-.02em] text-foreground">
          Consultando Siges
        </h2>
        <p aria-live="polite" className="font-body text-sm text-foreground">
          {etapaPorSegundos(segundos)}
        </p>
        <p className="font-body text-xs leading-relaxed text-muted-foreground">
          La primera carga recorre el historial completo de contadores (~10-15 segundos).
          Después queda en caché 10 minutos y la página responde al instante.
        </p>
        {segundos > 0 && (
          <p className="font-body text-xs tabular-nums text-muted-foreground/70">
            {segundos} s
          </p>
        )}
      </div>
    </div>
  );
}
