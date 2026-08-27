import { useState } from "react";

/** Estado + wrapper común de los modales de alta/edición: prende `saving`
 * mientras dura la acción, limpia el error al reintentar y lo deja en
 * `error` (para pasarlo al `error` prop de `BrandModal`) si falla. */
export function useModalSubmit() {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(action: () => Promise<void>, fallbackMessage = "Ocurrió un error."): Promise<void> {
    setSaving(true);
    setError(null);
    try {
      await action();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : fallbackMessage);
    } finally {
      setSaving(false);
    }
  }

  return { saving, error, setError, submit };
}
