import { afterEach, describe, expect, it, vi } from "vitest";
import { toast } from "sonner";
import type { ConversacionPendiente } from "../types/wati";
import { mostrarToastAtencion, retirarToast } from "./toast-atencion";

vi.mock("sonner", () => ({ toast: { warning: vi.fn(), dismiss: vi.fn() } }));

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

function pendiente(extra: Partial<ConversacionPendiente> = {}): ConversacionPendiente {
  return {
    wa_id: "549111",
    nombre: "Cliente SA",
    operador_nombre: "Ana",
    operador_email: "ana@x.com",
    sin_asignar: false,
    esperando_desde: "2026-10-01T12:00:00Z",
    minutos_esperando: 20,
    ultimo_mensaje_cliente_at: null,
    ultimo_texto_cliente: "hola",
    ...extra,
  };
}

const opciones = () => vi.mocked(toast.warning).mock.calls[0][1];

describe("toast de atención de WATI", () => {
  it("es persistente, se identifica por id y dice cuánto espera y quién lo tiene", () => {
    mostrarToastAtencion("t1", pendiente(), null);
    expect(vi.mocked(toast.warning).mock.calls[0][0]).toBe("Cliente SA espera respuesta hace 20 min");
    expect(opciones()).toMatchObject({
      id: "t1",
      description: "Asignado a Ana.",
      duration: Infinity,
      closeButton: true,
      action: undefined,
    });
  });

  it("avisa si el chat no está asignado y cae al email o a un guion si falta el nombre", () => {
    mostrarToastAtencion("t1", pendiente({ sin_asignar: true }), null);
    mostrarToastAtencion("t2", pendiente({ operador_nombre: null }), null);
    mostrarToastAtencion("t3", pendiente({ operador_nombre: null, operador_email: null }), null);
    const descripciones = vi.mocked(toast.warning).mock.calls.map((c) => c[1]?.description);
    expect(descripciones).toEqual(["Chat sin asignar — nadie lo tiene.", "Asignado a ana@x.com.", "Asignado a —."]);
  });

  it("con inbox configurado ofrece abrir WATI en otra pestaña", () => {
    const open = vi.fn();
    vi.stubGlobal("window", { open });
    mostrarToastAtencion("t1", pendiente(), "https://wati/inbox");
    const action = opciones()?.action as { label: string; onClick: () => void };
    expect(action.label).toBe("Abrir WATI");
    action.onClick();
    expect(open).toHaveBeenCalledWith("https://wati/inbox", "_blank", "noopener");
  });

  it("retirar el toast lo descarta por id", () => {
    retirarToast("t1");
    expect(toast.dismiss).toHaveBeenCalledWith("t1");
  });
});
