import Link from "next/link";

/** Submenú del ítem "Contadores" en el sidebar. Hoy tiene un solo hijo,
 * "Automatización" (el hub "Centro de Contadores" con las 8 herramientas
 * como cards + modal) — separado en su propio componente porque es donde
 * antes vivían los 8 links directos a cada herramienta. */
export function ContadoresNavSubmenu({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex flex-col gap-px py-1 pb-1.5 pl-6">
      <Link
        href="/contadores"
        onClick={onNavigate}
        aria-current="page"
        className="rounded-[6px] bg-brand-orange/[0.08] px-2 py-1.5 font-body text-[13px] text-brand-orange no-underline"
      >
        Automatización
      </Link>
    </div>
  );
}
