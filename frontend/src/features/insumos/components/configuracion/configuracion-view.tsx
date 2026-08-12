"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RotateCcw, Save, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";
import { BrandButton, BrandEmptyState, BrandSkeleton } from "@/shared/components/ui/brand-form";
import { useSession } from "@/services/session-provider";
import { useInsumosConfig } from "../../hooks/use-insumos-config";
import type { InsumosConfig } from "../../types";
import { ConfigNav } from "./config-nav";
import { ConfigSectionCard } from "./config-section-card";
import { CONFIG_SECTIONS, SECTION_BY_FIELD } from "./config-fields";
import { PreferencesCard } from "./preferences-card";
import {
  isDirty,
  toFormState,
  toPayload,
  type ConfigFieldKey,
  type ConfigFormState,
} from "./config-form";
import { hasErrors, validateConfigForm, type ConfigErrors } from "./config-validation";

/** Pantalla de Configuración de Insumos: los 17 parámetros de operación que
 * expone `/api/insumos/config`, agrupados en 6 secciones (Patrón 5 del
 * handoff: sidebar sticky + acordeón + footer de acciones).
 *
 * La validación client-side replica los rangos del backend para marcar el
 * campo culpable; si algo se escapa igual, el PUT vuelve con `{ok:false,error}`
 * (200, no excepción) y ese texto se muestra tal cual arriba del formulario. */

// Además de las 6 secciones del formulario, el sidebar y el observer de
// scroll también siguen a "Preferencias del navegador" (`preferences-card.tsx`),
// que no tiene campos de `ConfigResponse` y por eso no vive en `CONFIG_SECTIONS`.
const NAV_SECTIONS = [...CONFIG_SECTIONS, { id: "preferencias", title: "Preferencias del navegador" }];

function sectionIdOf(key: ConfigFieldKey): string {
  return SECTION_BY_FIELD[key];
}

function countErrorsBySection(errors: ConfigErrors): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const key of Object.keys(errors) as ConfigFieldKey[]) {
    const sectionId = sectionIdOf(key);
    counts[sectionId] = (counts[sectionId] ?? 0) + 1;
  }
  return counts;
}

export function ConfiguracionView() {
  const { can, user } = useSession();
  // `can()` solo refleja grants explícitos: un superadmin llega con la lista de
  // permisos vacía y sin este OR vería el formulario entero en solo lectura.
  const canUpdate = user.isSuperadmin || can("insumos", "update");
  const { config, loading, loadError, saving, saveError, save } = useInsumosConfig();

  const original = useMemo(() => (config ? toFormState(config) : null), [config]);
  const [form, setForm] = useState<ConfigFormState | null>(null);
  const [touched, setTouched] = useState<ReadonlySet<ConfigFieldKey>>(new Set());
  const [submitted, setSubmitted] = useState(false);
  const [openSections, setOpenSections] = useState<ReadonlySet<string>>(
    () => new Set(CONFIG_SECTIONS.map((section) => section.id)),
  );
  const [activeId, setActiveId] = useState(CONFIG_SECTIONS[0].id);

  // Resincroniza el formulario cada vez que llega una config nueva del backend
  // (carga inicial y relectura post-guardado). Mismo patrón de "ajustar estado
  // al cambiar una prop" que usa `ConfirmationModal`, sin efecto de por medio.
  const [syncedConfig, setSyncedConfig] = useState<InsumosConfig | null>(null);
  if (config !== syncedConfig) {
    setSyncedConfig(config);
    setForm(config ? toFormState(config) : null);
    setTouched(new Set());
    setSubmitted(false);
  }

  const errors = useMemo(() => (form ? validateConfigForm(form) : {}), [form]);
  const visibleErrors = useMemo<ConfigErrors>(() => {
    if (submitted) return errors;
    return Object.fromEntries(
      Object.entries(errors).filter(([key]) => touched.has(key as ConfigFieldKey)),
    );
  }, [errors, submitted, touched]);
  const errorCountBySection = useMemo(
    () => countErrorsBySection(visibleErrors),
    [visibleErrors],
  );

  const dirty = form !== null && original !== null && isDirty(form, original);

  const handleChange = useCallback(
    <K extends keyof ConfigFormState>(key: K, value: ConfigFormState[K]) => {
      setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
      setTouched((prev) => (prev.has(key) ? prev : new Set(prev).add(key)));
    },
    [],
  );

  const goToSection = useCallback((sectionId: string) => {
    setActiveId(sectionId);
    setOpenSections((prev) => (prev.has(sectionId) ? prev : new Set(prev).add(sectionId)));
    document
      .getElementById(`config-section-${sectionId}`)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  // La sección activa del sidebar sigue al scroll. El shell tiene su propio
  // contenedor con `overflow-y-auto`, pero IntersectionObserver mide contra el
  // viewport, así que funciona igual sin conocer ese contenedor.
  useEffect(() => {
    if (!form) return;
    const elements = NAV_SECTIONS.map((section) =>
      document.getElementById(`config-section-${section.id}`),
    ).filter((element): element is HTMLElement => element !== null);
    if (elements.length === 0) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((entry) => entry.isIntersecting);
        if (visible.length === 0) return;
        const topmost = visible.reduce((best, entry) =>
          entry.boundingClientRect.top < best.boundingClientRect.top ? entry : best,
        );
        setActiveId(topmost.target.id.replace("config-section-", ""));
      },
      { rootMargin: "-80px 0px -55% 0px" },
    );
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [form]);

  const handleSubmit = async () => {
    if (!form) return;
    setSubmitted(true);
    const currentErrors = validateConfigForm(form);
    if (hasErrors(currentErrors)) {
      const firstKey = Object.keys(currentErrors)[0] as ConfigFieldKey;
      toast.error("Revisá los campos marcados en rojo.");
      goToSection(sectionIdOf(firstKey));
      return;
    }
    await save(toPayload(form));
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-3 p-6 lg:p-10">
        <BrandSkeleton className="h-9 w-64" />
        {[0, 1, 2, 3].map((index) => (
          <BrandSkeleton key={index} className="h-24 w-full max-w-[720px]" />
        ))}
      </div>
    );
  }

  if (!form) {
    return (
      <div className="p-6 lg:p-10">
        <BrandEmptyState
          icon={SlidersHorizontal}
          title="No se pudo cargar la configuración."
          description={loadError ?? undefined}
        />
      </div>
    );
  }

  return (
    <div className="flex gap-8 p-6 lg:p-10">
      <ConfigNav
        sections={NAV_SECTIONS}
        activeId={activeId}
        errorCountBySection={errorCountBySection}
        onSelect={goToSection}
      />

      <div className="min-w-0 flex-1 lg:max-w-[720px]">
        <div className="mb-6">
          <h1 className="font-heading text-2xl font-extrabold text-foreground">
            Configuración de Insumos
          </h1>
          <p className="mt-1 font-body text-sm text-muted-foreground">
            Parámetros de operación del monitoreo y la carga de pedidos. Aplican a todos los
            clientes habilitados.
          </p>
        </div>

        {!canUpdate && (
          <div className="mb-4 rounded-[10px] border border-border bg-muted/50 px-4 py-3 font-body text-sm text-muted-foreground">
            Tenés permiso de lectura: podés ver los parámetros pero no modificarlos.
          </div>
        )}

        {saveError && (
          <div className="mb-4 rounded-[10px] border border-[rgba(239,68,68,.25)] bg-[rgba(239,68,68,.07)] px-4 py-3 font-body text-sm font-semibold text-[#991b1b] dark:text-[#fca5a5]">
            {saveError}
          </div>
        )}

        <div className="flex flex-col gap-3.5">
          {CONFIG_SECTIONS.map((section) => (
            <ConfigSectionCard
              key={section.id}
              section={section}
              open={openSections.has(section.id)}
              onToggle={() =>
                setOpenSections((prev) => {
                  const next = new Set(prev);
                  if (next.has(section.id)) next.delete(section.id);
                  else next.add(section.id);
                  return next;
                })
              }
              form={form}
              errors={visibleErrors}
              errorCount={errorCountBySection[section.id] ?? 0}
              disabled={!canUpdate || saving}
              onChange={handleChange}
            />
          ))}

          <PreferencesCard />
        </div>

        <div className="sticky bottom-0 -mx-1 mt-6 flex items-center justify-end gap-3 border-t border-border bg-background px-1 py-4">
          {dirty && (
            <span className="mr-auto font-body text-xs text-muted-foreground">
              Hay cambios sin guardar.
            </span>
          )}
          <BrandButton
            variant="outline"
            disabled={!dirty || saving}
            onClick={() => {
              if (original) setForm(original);
              setTouched(new Set());
              setSubmitted(false);
            }}
          >
            <RotateCcw className="h-4 w-4" />
            Descartar
          </BrandButton>
          <BrandButton
            onClick={() => void handleSubmit()}
            loading={saving}
            disabled={!canUpdate || !dirty}
          >
            {!saving && <Save className="h-4 w-4" />}
            Guardar cambios
          </BrandButton>
        </div>
      </div>
    </div>
  );
}
