"use client";

import { Switch } from "@/shared/components/ui/switch";
import { useDesktopNotifications } from "../../hooks/use-desktop-notifications";

/** Card de "Preferencias del navegador" (Configuración de Insumos): toggle de
 * notificaciones de escritorio para solicitudes nuevas sin cargar. Mismo
 * chrome que `ConfigSectionCard` pero SIN acordeón — un solo control no
 * necesita colapsar — y por eso vive en su propio archivo en vez de sumarse a
 * `CONFIG_SECTIONS` (esas 6 secciones son un espejo estricto de los 17 campos
 * de `ConfigResponse`, atados a `isDirty`/`toPayload`/"Guardar cambios").
 *
 * La preferencia se guarda sola en `localStorage`, no depende del footer de
 * Guardar cambios de la pantalla — de ahí el sub-label fijo.
 */

const WARNING_TEXT: Partial<Record<string, string>> = {
  unsupported:
    "Tu navegador no expone notificaciones de escritorio en esta página. Suele pasar cuando la app se sirve por HTTP en vez de HTTPS — avisale a sistemas.",
  denied:
    "Bloqueaste las notificaciones para este sitio. Habilitalas desde el candado de la barra de direcciones.",
};

export function PreferencesCard() {
  const desktop = useDesktopNotifications();

  if (!desktop.mounted) return null;

  const disabled = desktop.support === "unsupported" || desktop.support === "denied";
  const warning = WARNING_TEXT[desktop.support];

  return (
    <section
      id="config-section-preferencias"
      className="scroll-mt-6 overflow-hidden rounded-[12px] border border-border bg-card"
    >
      <div className="flex items-center gap-3 px-5 py-4">
        <span className="flex-1 font-heading text-[15px] font-bold text-foreground">
          Preferencias del navegador
        </span>
      </div>

      <div className="flex flex-col gap-3 border-t border-border px-5 py-5">
        <div className="flex items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <span className="font-body text-sm font-semibold text-foreground">
              Notificaciones de escritorio
            </span>
            <span className="font-body text-[13px] leading-relaxed text-muted-foreground">
              Avisa en este navegador cuando aparecen solicitudes de insumos nuevas sin cargar.
            </span>
          </div>
          <Switch
            checked={desktop.enabled}
            onCheckedChange={(value) => void desktop.setEnabled(value)}
            disabled={disabled}
            label="Notificaciones de escritorio"
          />
        </div>

        {warning && (
          <p className="font-body text-[13px] leading-relaxed text-[#dc2626] dark:text-[#f87171]">
            {warning}
          </p>
        )}

        <p className="font-body text-xs text-muted-foreground">
          Preferencia de este navegador. Se guarda sola, no depende de «Guardar cambios».
        </p>
      </div>
    </section>
  );
}
