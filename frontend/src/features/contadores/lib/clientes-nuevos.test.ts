import { afterEach, describe, expect, it, vi } from "vitest";
import type { CandidatoClienteNuevo, ClienteNuevo, ResumenSigesClienteNuevo } from "../types/clientes-nuevos";
import {
  coincideBusqueda, cumpleFiltro, detalleInstalados, formatFecha, hoyIso, payloadDesdeCandidato, textoInstalados,
} from "./clientes-nuevos";

const siges = (over: Partial<ResumenSigesClienteNuevo> = {}): ResumenSigesClienteNuevo => ({
  empresa_id: 7, equipos_despachados: 12, ultimo_despacho: "2026-08-10", equipos_instalados: 6,
  ultima_instalacion: "2026-08-21", equipos_con_toma: 5, instalas: 4, contrato_nro: "C-99",
  fecha_firma: null, vendedor: "Laura Gómez", rubro: "IMPRESION", ...over,
});

const ficha = (over: Partial<ClienteNuevo> = {}): ClienteNuevo =>
  ({
    id: "1", cliente: "Acme SA", siges_empresa_id: null, contrato_nro: "A-1", vendedor: null,
    operador_id: null, notas: null, estado: "ESPERANDO_INSTALACION", equipos_previstos: null, siges: null, ...over,
  }) as ClienteNuevo;

afterEach(() => {
  vi.useRealTimers();
});

describe("filtros del tablero de clientes nuevos", () => {
  it("'abiertas' muestra todo menos lo cerrado y 'todas' no filtra", () => {
    expect(cumpleFiltro(ficha({ estado: "STC_ENVIADO" }), "abiertas")).toBe(true);
    expect(cumpleFiltro(ficha({ estado: "CERRADO" }), "abiertas")).toBe(false);
    expect(cumpleFiltro(ficha({ estado: "CERRADO" }), "todas")).toBe(true);
  });

  it("un estado puntual filtra exacto", () => {
    expect(cumpleFiltro(ficha({ estado: "STC_PENDIENTE" }), "STC_PENDIENTE")).toBe(true);
    expect(cumpleFiltro(ficha({ estado: "STC_ENVIADO" }), "STC_PENDIENTE")).toBe(false);
  });

  it("busca en cliente, contrato, vendedor, notas y en lo que trae Siges", () => {
    const f = ficha({ notas: "Llamar a Pedro", siges: siges({ vendedor: "Laura Gómez" }) });
    expect(coincideBusqueda(f, "")).toBe(true);
    expect(coincideBusqueda(f, "acme")).toBe(true);
    expect(coincideBusqueda(f, "pedro")).toBe(true);
    expect(coincideBusqueda(f, "laura")).toBe(true);
    expect(coincideBusqueda(f, "c-99")).toBe(true);
    expect(coincideBusqueda(f, "inexistente")).toBe(false);
  });
});

describe("fechas de clientes nuevos", () => {
  it("muestra la fecha pura como dd/mm/aaaa, también si viene con hora, y '—' sin dato", () => {
    expect(formatFecha("2026-08-06")).toBe("06/08/2026");
    expect(formatFecha("2026-08-06T23:30:00Z")).toBe("06/08/2026");
    expect(formatFecha(null)).toBe("—");
    expect(formatFecha("")).toBe("—");
  });

  it("hoy es el día local de Argentina, no el de UTC", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-08-07T01:30:00Z"));
    expect(hoyIso()).toBe("2026-08-06");
  });
});

describe("precarga desde una sugerencia de Siges", () => {
  it("trae cliente, empresa, contrato, firma y vendedor, pero no los equipos previstos", () => {
    const c: CandidatoClienteNuevo = {
      empresa_id: 7, cliente: "Acme SA", contrato_nro: "C-99", fecha_firma: "2026-08-01",
      vendedor: "Laura", rubro: "IT", equipos_despachados: 12,
    };
    const p = payloadDesdeCandidato(c);
    expect(p).toMatchObject({
      cliente: "Acme SA", siges_empresa_id: 7, contrato_nro: "C-99", fecha_firma: "2026-08-01",
      vendedor: "Laura", estado: "ESPERANDO_INSTALACION",
    });
    expect(p.equipos_previstos).toBeNull();
  });
});

describe("avance de instalación", () => {
  it("distingue ficha sin cruce de Siges sin respuesta", () => {
    expect(textoInstalados(ficha())).toBe("Sin cruce");
    expect(textoInstalados(ficha({ siges_empresa_id: 7 }))).toBe("Siges sin respuesta");
  });

  it("avisa cuando Equipamiento todavía no despachó nada", () => {
    expect(textoInstalados(ficha({ siges: siges({ equipos_despachados: 0 }) }))).toBe("Sin despachos");
  });

  it("muestra instaladas sobre despachadas y la última instalación si la hay", () => {
    expect(textoInstalados(ficha({ siges: siges() }))).toBe("6 / 12 instaladas · últ. 21/08/2026");
    expect(textoInstalados(ficha({ siges: siges({ ultima_instalacion: null }) }))).toBe("6 / 12 instaladas");
  });

  it("detalla despachos, tomas, órdenes y previstas en el tooltip, omitiendo lo que falta", () => {
    expect(detalleInstalados(ficha())).toBe("");
    expect(detalleInstalados(ficha({ siges: siges(), equipos_previstos: 10 }))).toBe(
      "12 despachadas por Equipamiento · último despacho 10/08/2026 · 5 con toma real · 4 órdenes de instalación · 10 previstas según el mail",
    );
    expect(detalleInstalados(ficha({ siges: siges({ ultimo_despacho: null }) }))).toBe(
      "12 despachadas por Equipamiento · 5 con toma real · 4 órdenes de instalación",
    );
  });
});
