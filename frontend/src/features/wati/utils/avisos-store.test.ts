import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ConversacionPendiente } from "../types/wati";

const KEY = "wati-alertas-avisadas";
let storage: Map<string, string>;

// El store guarda estado a nivel módulo: cada test importa una instancia nueva.
async function cargarStore() {
  vi.resetModules();
  return import("./avisos-store");
}

beforeEach(() => {
  storage = new Map();
  vi.stubGlobal("sessionStorage", {
    getItem: (k: string) => storage.get(k) ?? null,
    setItem: (k: string, v: string) => void storage.set(k, v),
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("registro de avisos de WATI confirmados", () => {
  it("la clave es wa_id y nivel", async () => {
    const { claveAviso } = await cargarStore();
    expect(claveAviso({ wa_id: "549111" } as ConversacionPendiente, "critico")).toBe("549111:critico");
  });

  it("recupera lo confirmado antes de recargar la pestaña", async () => {
    storage.set(KEY, JSON.stringify(["a:critico"]));
    const { avisosStore } = await cargarStore();
    expect([...avisosStore.getSnapshot()]).toEqual(["a:critico"]);
  });

  it("confirmar agrega claves, persiste y avisa a los suscriptores con un Set nuevo", async () => {
    const { avisosStore } = await cargarStore();
    const antes = avisosStore.getSnapshot();
    const listener = vi.fn();
    const desuscribir = avisosStore.subscribe(listener);
    avisosStore.confirmar(["a:atencion", "b:critico"]);
    expect(listener).toHaveBeenCalledTimes(1);
    expect(avisosStore.getSnapshot()).not.toBe(antes);
    expect(JSON.parse(storage.get(KEY) ?? "[]")).toEqual(["a:atencion", "b:critico"]);
    desuscribir();
    avisosStore.confirmar(["c:critico"]);
    expect(listener).toHaveBeenCalledTimes(1);
  });

  it("confirmar sin claves no publica nada", async () => {
    const { avisosStore } = await cargarStore();
    const listener = vi.fn();
    avisosStore.subscribe(listener);
    avisosStore.confirmar([]);
    expect(listener).not.toHaveBeenCalled();
  });

  it("olvida las claves que dejaron de estar vigentes y no publica si no cambió nada", async () => {
    storage.set(KEY, JSON.stringify(["a:critico", "b:critico"]));
    const { avisosStore } = await cargarStore();
    const listener = vi.fn();
    avisosStore.subscribe(listener);
    avisosStore.conservarSolo(new Set(["a:critico", "b:critico", "c:critico"]));
    expect(listener).not.toHaveBeenCalled();
    avisosStore.conservarSolo(new Set(["b:critico"]));
    expect(listener).toHaveBeenCalledTimes(1);
    expect([...avisosStore.getSnapshot()]).toEqual(["b:critico"]);
    expect(storage.get(KEY)).toBe('["b:critico"]');
  });

  it("con datos corruptos o sin sessionStorage arranca vacío y sigue funcionando en memoria", async () => {
    storage.set(KEY, "{no es json");
    let { avisosStore } = await cargarStore();
    expect(avisosStore.getSnapshot().size).toBe(0);

    vi.unstubAllGlobals(); // node no tiene sessionStorage
    ({ avisosStore } = await cargarStore());
    avisosStore.confirmar(["a:critico"]);
    expect([...avisosStore.getSnapshot()]).toEqual(["a:critico"]);
  });

  it("en el servidor el snapshot siempre está vacío", async () => {
    storage.set(KEY, JSON.stringify(["a:critico"]));
    const { avisosStore } = await cargarStore();
    expect(avisosStore.getServerSnapshot().size).toBe(0);
  });
});
