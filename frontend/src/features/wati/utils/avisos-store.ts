import type { ConversacionPendiente } from "../types/wati";
import type { NivelEspera } from "./espera";

const STORAGE_KEY = "wati-alertas-avisadas";

export function claveAviso(p: ConversacionPendiente, nivel: NivelEspera): string {
  return `${p.wa_id}:${nivel}`;
}

function leer(): ReadonlySet<string> {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    return new Set();
  }
}

function guardar(confirmadas: ReadonlySet<string>): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...confirmadas]));
  } catch {
    // sessionStorage no disponible: el registro vive solo en memoria.
  }
}

const VACIO: ReadonlySet<string> = new Set();
let snapshot: ReadonlySet<string> | null = null;
const listeners = new Set<() => void>();

function publicar(siguiente: ReadonlySet<string>): void {
  snapshot = siguiente;
  guardar(siguiente);
  listeners.forEach((l) => l());
}

/** Registro de avisos de WATI ya confirmados por el operador (clave
 * `wa_id:nivel`), como store externo para `useSyncExternalStore`: se muta
 * desde efectos y handlers sin `setState` en efectos, y persiste en
 * sessionStorage para sobrevivir una recarga de la pestaña. Cada mutación
 * publica un Set nuevo (inmutable) para que React detecte el cambio. */
export const avisosStore = {
  subscribe(listener: () => void): () => void {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
  getSnapshot(): ReadonlySet<string> {
    snapshot ??= leer();
    return snapshot;
  },
  getServerSnapshot(): ReadonlySet<string> {
    return VACIO;
  },
  confirmar(claves: string[]): void {
    if (claves.length === 0) return;
    publicar(new Set([...avisosStore.getSnapshot(), ...claves]));
  },
  /** Olvida las claves que ya no están vigentes (el chat se respondió o
   * cerró): si vuelve a esperar, se avisa de nuevo. */
  conservarSolo(vigentes: ReadonlySet<string>): void {
    const actual = avisosStore.getSnapshot();
    const filtradas = [...actual].filter((k) => vigentes.has(k));
    if (filtradas.length === actual.size) return;
    publicar(new Set(filtradas));
  },
};
