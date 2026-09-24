import type { ReclamoOca } from "../../types/despachados";

/** Formulario público de reclamos para grandes cuentas de OCA
 * (https://int.oca.com.ar/grandescuentas/). No es una API: es un formulario
 * CRM de Bitrix24 que esa página incrusta, y acá se incrusta igual. Todo lo
 * que depende de Bitrix (URL del loader, id del formulario, nombres de los
 * campos) vive en este archivo: si OCA cambia el formulario, se corrige acá.
 * Relevado el 2026-09-24. */
export const OCA_FORM = {
  paginaPublica: "https://int.oca.com.ar/grandescuentas/",
  /** Valor de `data-b24-form` del `<script>` que marca dónde se dibuja. */
  dataB24Form: "inline/65/x0s3es",
  formId: "65",
  loaderUrl: "https://cdn.bitrix24.es/b22492375/crm/form/loader_65.js",
  /** Etiqueta del motivo que se elige (la lista tiene ids internos de Bitrix). */
  motivo: "Otros motivos",
  /** Si en este tiempo no apareció el formulario, se muestra el respaldo. */
  esperaMs: 15_000,
} as const;

/** Nombre de cada campo del formulario de Bitrix24. */
const CAMPO = {
  nombre: "CONTACT_NAME",
  apellido: "CONTACT_LAST_NAME",
  empresa: "DEAL_UF_CRM_64957AA2A3018",
  cuit: "DEAL_UF_CRM_649498F0BA6E0",
  telefono: "CONTACT_UF_CRM_1680638045",
  email: "CONTACT_EMAIL",
  guia: "DEAL_UF_CRM_1706538148644",
  motivo: "DEAL_UF_CRM_1688475304058",
  comentario: "DEAL_COMMENTS",
} as const;

interface CampoB24 {
  name: string;
  items?: { value: string; label: string }[];
}

/** Lo que se usa de un formulario de Bitrix24 (`b24form.App.list()`). */
export interface FormularioB24 {
  identification?: { id?: string };
  setValues: (valores: Record<string, string>) => void;
  getFields: () => CampoB24[];
  destroy?: () => void;
}

interface B24Global {
  App?: { list: () => FormularioB24[] };
}

/** Los formularios de OCA que Bitrix24 tiene dibujados en la página. */
export function formulariosOca(): FormularioB24[] {
  const app = (window as unknown as { b24form?: B24Global }).b24form?.App;
  return (app?.list() ?? []).filter((f) => f.identification?.id === OCA_FORM.formId);
}

/** Id interno del motivo "Otros motivos" en la lista del formulario. */
function idMotivo(form: FormularioB24): string | undefined {
  const campo = form.getFields().find((c) => c.name === CAMPO.motivo);
  return campo?.items?.find((i) => i.label === OCA_FORM.motivo)?.value;
}

/** Datos de dominio -> valores del formulario. Los vacíos no se mandan (así no
 * se pisa nada con ""); sin contacto van solo la guía y el comentario. */
export function valoresFormulario(reclamo: ReclamoOca, form: FormularioB24): Record<string, string> {
  const c = reclamo.contacto;
  const valores: Record<string, string | undefined> = {
    [CAMPO.nombre]: c?.nombre,
    [CAMPO.apellido]: c?.apellido,
    [CAMPO.empresa]: c?.empresa,
    [CAMPO.cuit]: c?.cuit,
    [CAMPO.telefono]: c?.telefono,
    [CAMPO.email]: c?.email,
    [CAMPO.guia]: reclamo.guia,
    [CAMPO.motivo]: idMotivo(form),
    [CAMPO.comentario]: reclamo.comentario,
  };
  return Object.fromEntries(Object.entries(valores).filter((e): e is [string, string] => !!e[1]));
}

/** Dibuja el formulario dentro de `contenedor`: el `<script data-b24-form>`
 * marca el lugar y el loader de Bitrix24 lo renderiza ahí. El loader (7 KB) se
 * vuelve a inyectar en cada apertura porque es el que dispara el dibujo; la
 * app pesada de Bitrix24 no se recarga (su Loader la detecta en
 * `window.b24form`). Devuelve la limpieza: destruye el formulario, saca el
 * loader y vacía el contenedor. */
export function montarFormularioOca(contenedor: HTMLElement, onError: () => void): () => void {
  const marca = document.createElement("script");
  marca.setAttribute("data-b24-form", OCA_FORM.dataB24Form);
  marca.setAttribute("data-skip-moving", "true");
  contenedor.appendChild(marca);
  const loader = document.createElement("script");
  loader.async = true;
  loader.src = `${OCA_FORM.loaderUrl}?${(Date.now() / 180_000) | 0}`;
  loader.dataset.hdmReclamoOca = "";
  loader.onerror = onError;
  document.head.appendChild(loader);
  return () => {
    formulariosOca().forEach((f) => f.destroy?.());
    loader.remove();
    contenedor.replaceChildren();
  };
}

/** Espera a que Bitrix24 dibuje el formulario: el evento `b24:form:init` o,
 * por las dudas, un sondeo de `b24form.App.list()`. Rechaza a los `esperaMs`. */
export function esperarFormularioOca(esperaMs: number = OCA_FORM.esperaMs): {
  promesa: Promise<FormularioB24>;
  cancelar: () => void;
} {
  let cancelar = () => {};
  const promesa = new Promise<FormularioB24>((resolve, reject) => {
    const listo = (form: FormularioB24) => {
      cancelar();
      resolve(form);
    };
    const alEvento = (e: Event) => {
      const form = (e as CustomEvent<{ object?: FormularioB24 }>).detail?.object;
      if (form?.identification?.id === OCA_FORM.formId) listo(form);
    };
    const sondeo = window.setInterval(() => {
      const form = formulariosOca().at(-1);
      if (form) listo(form);
    }, 250);
    const limite = window.setTimeout(() => {
      cancelar();
      reject(new Error("El formulario de OCA no cargó a tiempo"));
    }, esperaMs);
    window.addEventListener("b24:form:init", alEvento);
    cancelar = () => {
      window.clearInterval(sondeo);
      window.clearTimeout(limite);
      window.removeEventListener("b24:form:init", alEvento);
    };
  });
  return { promesa, cancelar };
}
