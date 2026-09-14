// El Clipboard API moderno (`navigator.clipboard`) exige "contexto seguro"
// (`https` o `localhost`); los compañeros que entran por IP de red en `http`
// (ej. `http://192.168.x.x:3000`) no lo tienen, y `writeText`/`write`
// rechazan la promesa. Fallback: `document.execCommand("copy")` sobre un
// listener del evento `copy`, que no tiene esa restricción — deprecado pero
// soportado en Chrome/Edge/Firefox, y es el workaround estándar para apps
// intranet servidas por HTTP plano.

function copiarViaExecCommand(datos: Record<string, string>): boolean {
  const listener = (e: ClipboardEvent) => {
    e.preventDefault();
    for (const [tipo, valor] of Object.entries(datos)) {
      e.clipboardData?.setData(tipo, valor);
    }
  };
  document.addEventListener("copy", listener);
  try {
    return document.execCommand("copy");
  } finally {
    document.removeEventListener("copy", listener);
  }
}

export async function copiarTexto(texto: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(texto);
      return;
    } catch {
      // contexto no seguro u otro rechazo: seguimos al fallback
    }
  }
  if (!copiarViaExecCommand({ "text/plain": texto })) {
    throw new Error("No se pudo copiar");
  }
}

export async function copiarHtmlYTexto(html: string, texto: string): Promise<void> {
  if (navigator.clipboard?.write && typeof ClipboardItem !== "undefined") {
    try {
      await navigator.clipboard.write([
        new ClipboardItem({
          "text/html": new Blob([html], { type: "text/html" }),
          "text/plain": new Blob([texto], { type: "text/plain" }),
        }),
      ]);
      return;
    } catch {
      // contexto no seguro, sin soporte de ClipboardItem, u otro rechazo
    }
  }
  if (!copiarViaExecCommand({ "text/html": html, "text/plain": texto })) {
    throw new Error("No se pudo copiar");
  }
}
