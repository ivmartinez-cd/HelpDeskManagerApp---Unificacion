"use client";

import { useState } from "react";
import { Switch } from "@/shared/components/ui/switch";
import { useDesktopNotifications } from "../../hooks/use-desktop-notifications";
import type { NotificationSupport } from "../../hooks/use-desktop-notifications";

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

const PERMISSION_LABEL: Record<NotificationSupport, string> = {
  unsupported: "No soportado",
  granted: "Permitido",
  denied: "Bloqueado",
  default: "No solicitado",
};

const PERMISSION_CLASS: Record<NotificationSupport, string> = {
  unsupported: "text-[#dc2626] dark:text-[#f87171]",
  denied: "text-[#dc2626] dark:text-[#f87171]",
  granted: "text-[#16a34a] dark:text-[#4ade80]",
  default: "text-[#a16207] dark:text-[#facc15]",
};

const BROWSER_SETTINGS_URL = "chrome://settings/content/notifications";

export function PreferencesCard() {
  const desktop = useDesktopNotifications();
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  if (!desktop.mounted) return null;

  const disabled = desktop.support === "unsupported" || desktop.support === "denied";
  const warning = WARNING_TEXT[desktop.support];

  async function handleTest() {
    setTesting(true);
    try {
      setTestMessage(await desktop.sendTestNotification());
    } finally {
      setTesting(false);
    }
  }

  async function handleCopyBrowserUrl() {
    try {
      await navigator.clipboard.writeText(BROWSER_SETTINGS_URL);
      setTestMessage("Dirección copiada — pegala en la barra de direcciones.");
    } catch {
      setTestMessage("No se pudo copiar. Escribila manualmente en la barra de direcciones.");
    }
  }

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

        <div className="mt-1 flex flex-col gap-3 border-t border-border pt-4">
          <div className="flex flex-wrap items-center gap-4">
            <button
              type="button"
              onClick={() => void handleTest()}
              disabled={testing}
              className="rounded-[8px] border border-border bg-card px-3 py-1.5 font-body text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-50"
            >
              Probar notificación
            </button>
            <span className="font-body text-xs text-muted-foreground">
              Estado del permiso:{" "}
              <strong className={PERMISSION_CLASS[desktop.support]}>
                {PERMISSION_LABEL[desktop.support]}
              </strong>
            </span>
          </div>

          {testMessage && <p className="font-body text-xs text-muted-foreground">{testMessage}</p>}

          <div className="border-t border-border pt-3">
            <p className="mb-2 font-body text-xs text-muted-foreground">
              ¿Le diste «Permitir» arriba pero igual no te aparece la notificación de Windows?
              Revisá estos lugares:
            </p>
            <ol className="list-inside list-decimal space-y-1.5 font-body text-xs text-muted-foreground">
              <li>
                Si el estado de arriba dice «Bloqueado» o «No solicitado», el sitio no tiene
                permiso en el navegador:
                <div className="ml-4 mt-1 flex items-center gap-2">
                  <code className="rounded bg-muted px-1.5 py-0.5 text-[11px]">
                    {BROWSER_SETTINGS_URL}
                  </code>
                  <button
                    type="button"
                    onClick={() => void handleCopyBrowserUrl()}
                    className="text-brand-orange hover:underline"
                  >
                    Copiar
                  </button>
                </div>
                <span className="ml-4 block">
                  pegalo en la barra de direcciones del navegador (Chrome y Edge redirigen a su
                  propia página) y activá las notificaciones para este sitio.
                </span>
              </li>
              <li>
                <a
                  href="ms-settings:notifications"
                  className="text-brand-orange hover:underline"
                >
                  Configuración de Windows → Notificaciones
                </a>{" "}
                — buscá el navegador en la lista y verificá que esté en «Activado».
              </li>
              <li>
                <a href="ms-settings:quiethours" className="text-brand-orange hover:underline">
                  Configuración de Windows → Asistente de concentración
                </a>{" "}
                — si está en «Solo alarmas» o «Solo notificaciones prioritarias», Windows oculta
                el aviso aunque el navegador lo mande.
              </li>
            </ol>
            <p className="mt-2 font-body text-xs text-muted-foreground">
              Los links abren directo la Configuración de Windows (puede pedir confirmación del
              sistema).
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
