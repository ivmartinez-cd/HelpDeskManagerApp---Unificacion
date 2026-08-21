"use client";

import { useEffect, useState } from "react";
import { ApiError } from "@/services/http-client";
import { clientesNuevosApi } from "../api/clientes-nuevos-api";
import { contadoresApi } from "../api/contadores-api";
import type { EmpresaSiges, Operador } from "../types/calendario";
import type { ClienteNuevo, ClienteNuevoPayload, EstadoClienteNuevo } from "../types/clientes-nuevos";
import { ESTADOS, ESTADO_META, PAYLOAD_VACIO, hoyIso, payloadDesdeFicha } from "../lib/clientes-nuevos";
import { BrandButton, BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { BrandModal } from "@/shared/components/ui/brand-modal";

interface ClienteNuevoModalProps {
  /** Con ficha = edición in-place; sin ficha, alta (con `inicial` opcional,
   * ej. precargada desde una sugerencia de Siges). */
  ficha: ClienteNuevo | null;
  inicial?: ClienteNuevoPayload | null;
  operadores: Operador[];
  onClose: () => void;
  onSaved: () => void;
}

const labelClass = "font-body text-[11px] font-bold uppercase tracking-wide text-muted-foreground";
const fieldClass =
  "rounded-[8px] border border-border bg-card px-[14px] py-[9px] font-body text-sm text-foreground outline-none focus:ring-2 focus:ring-brand-orange/40";

function SigesPicker({
  empresaId,
  onChange,
}: {
  empresaId: number | null;
  onChange: (empresa: EmpresaSiges | null) => void;
}) {
  const [q, setQ] = useState("");
  const [resultados, setResultados] = useState<EmpresaSiges[]>([]);
  const [buscando, setBuscando] = useState(false);

  useEffect(() => {
    const texto = q.trim();
    // 350 ms de inactividad antes de pegarle a Siges; con menos de 2 letras
    // solo se limpia la lista (dentro del timer, no en el cuerpo del efecto).
    const timer = setTimeout(() => {
      if (texto.length < 2) {
        setResultados([]);
        return;
      }
      setBuscando(true);
      contadoresApi
        .searchEmpresasSiges(texto)
        .then(setResultados)
        .catch((err: unknown) => {
          console.error("Error buscando empresas en Siges:", err);
          setResultados([]);
        })
        .finally(() => setBuscando(false));
    }, 350);
    return () => clearTimeout(timer);
  }, [q]);

  return (
    <div className="flex flex-col gap-1.5">
      <BrandInput
        label="Empresa en Siges (para ver instalaciones)"
        type="search"
        placeholder="Buscá por nombre comercial…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        hint={
          empresaId
            ? `Cruzada con ID_Empresa ${empresaId}. Buscá otra para cambiarla.`
            : "Sin cruce: la ficha no muestra instalaciones de Siges."
        }
      />
      {(resultados.length > 0 || buscando) && (
        <ul className="max-h-40 overflow-y-auto rounded-[8px] border border-border bg-card">
          {buscando && (
            <li className="px-3 py-2 font-body text-xs text-muted-foreground">Buscando…</li>
          )}
          {resultados.map((e) => (
            <li key={e.id}>
              <button
                type="button"
                onClick={() => {
                  onChange(e);
                  setQ("");
                  setResultados([]);
                }}
                className="flex w-full items-center justify-between px-3 py-2 text-left font-body text-sm text-foreground hover:bg-muted"
              >
                <span className="truncate">{e.den_comercial}</span>
                <span className="ml-3 shrink-0 text-xs text-muted-foreground">
                  #{e.id} · {e.impresoras} impr.
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {empresaId && (
        <button
          type="button"
          onClick={() => onChange(null)}
          className="self-start font-body text-xs text-muted-foreground hover:text-brand-orange"
        >
          Quitar cruce con Siges
        </button>
      )}
    </div>
  );
}

export function ClienteNuevoModal({
  ficha,
  inicial = null,
  operadores,
  onClose,
  onSaved,
}: ClienteNuevoModalProps) {
  const [form, setForm] = useState<ClienteNuevoPayload>(
    ficha ? payloadDesdeFicha(ficha) : (inicial ?? PAYLOAD_VACIO),
  );
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const set = <K extends keyof ClienteNuevoPayload>(key: K, value: ClienteNuevoPayload[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }));
  const texto = (v: string): string | null => (v.trim() ? v : null);
  const numero = (v: string): number | null => (v === "" ? null : Number(v));

  const completo = form.cliente.trim().length > 0;

  const handleSubmit = () => {
    if (!completo) return;
    setSaving(true);
    setSaveError(null);
    const payload: ClienteNuevoPayload = {
      ...form,
      // Si pasa a "STC enviado" sin fecha, se toma hoy.
      stc_enviado_el:
        form.estado === "STC_ENVIADO" ? (form.stc_enviado_el ?? hoyIso()) : form.stc_enviado_el,
    };
    (ficha ? clientesNuevosApi.update(ficha.id, payload) : clientesNuevosApi.create(payload))
      .then(onSaved)
      .catch((err: unknown) => {
        console.error("Error al guardar la ficha:", err);
        setSaveError(err instanceof ApiError ? err.message : "No se pudo guardar la ficha.");
      })
      .finally(() => setSaving(false));
  };

  return (
    <BrandModal
      isOpen
      onClose={onClose}
      title={ficha ? "Editar ficha" : "Nueva ficha de cliente"}
      widthPx={640}
      error={saveError}
    >
      <div className="flex flex-col gap-4">
        <BrandInput
          label="Cliente"
          value={form.cliente}
          onChange={(e) => set("cliente", e.target.value)}
          placeholder="Como figura en el mail de Comercial"
          required
          autoFocus
        />
        <SigesPicker
          empresaId={form.siges_empresa_id}
          onChange={(e) => {
            set("siges_empresa_id", e ? e.id : null);
            if (e && !form.cliente.trim()) set("cliente", e.den_comercial);
          }}
        />
        <div className="grid grid-cols-2 gap-3">
          <BrandInput
            label="Contrato N°"
            value={form.contrato_nro ?? ""}
            onChange={(e) => set("contrato_nro", texto(e.target.value))}
          />
          <BrandInput
            label="Fecha de firma"
            type="date"
            value={form.fecha_firma ?? ""}
            onChange={(e) => set("fecha_firma", texto(e.target.value))}
          />
          <BrandInput
            label="Vendedor / ejecutivo"
            value={form.vendedor ?? ""}
            onChange={(e) => set("vendedor", texto(e.target.value))}
            placeholder="AV, GL, EA…"
          />
          <BrandInput
            label="Implementación de servicio"
            value={form.implementacion_servicio ?? ""}
            onChange={(e) => set("implementacion_servicio", texto(e.target.value))}
            placeholder="MPS"
          />
          <BrandInput
            label="Implementación estimada"
            type="date"
            value={form.fecha_estimada_implementacion ?? ""}
            onChange={(e) => set("fecha_estimada_implementacion", texto(e.target.value))}
          />
          <BrandInput
            label="1ª facturación estimada"
            type="date"
            value={form.fecha_estimada_primera_facturacion ?? ""}
            onChange={(e) => set("fecha_estimada_primera_facturacion", texto(e.target.value))}
          />
          <BrandInput
            label="Equipos previstos"
            type="number"
            min={0}
            value={form.equipos_previstos ?? ""}
            onChange={(e) => set("equipos_previstos", numero(e.target.value))}
          />
          <BrandInput
            label="Día de corte (vacío = a definir)"
            type="number"
            min={1}
            max={31}
            value={form.dia_corte ?? ""}
            onChange={(e) => set("dia_corte", numero(e.target.value))}
          />
          <BrandSelect
            label="Operador"
            value={form.operador_id ?? ""}
            onChange={(e) => set("operador_id", texto(e.target.value))}
          >
            <option value="">Sin asignar</option>
            {operadores.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nombre}
              </option>
            ))}
          </BrandSelect>
          <BrandSelect
            label="Estado"
            value={form.estado}
            onChange={(e) => set("estado", e.target.value as EstadoClienteNuevo)}
          >
            {ESTADOS.map((e) => (
              <option key={e} value={e}>
                {ESTADO_META[e].label}
              </option>
            ))}
          </BrandSelect>
          {form.estado === "STC_ENVIADO" && (
            <BrandInput
              label="STC enviado el"
              type="date"
              value={form.stc_enviado_el ?? ""}
              onChange={(e) => set("stc_enviado_el", texto(e.target.value))}
            />
          )}
        </div>
        <div className="flex flex-col gap-1.5">
          <label htmlFor="cliente-nuevo-notas" className={labelClass}>
            Situación / notas
          </label>
          <textarea
            id="cliente-nuevo-notas"
            rows={3}
            maxLength={1000}
            value={form.notas ?? ""}
            onChange={(e) => set("notas", texto(e.target.value))}
            placeholder="Ej. FE 1º FC 01/10 · instalaciones 20/08 · falta confirmar contacto"
            className={fieldClass}
          />
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <BrandButton variant="outline" onClick={onClose} disabled={saving}>
            Cancelar
          </BrandButton>
          <BrandButton onClick={handleSubmit} loading={saving} disabled={!completo}>
            {ficha ? "Guardar cambios" : "Crear ficha"}
          </BrandButton>
        </div>
      </div>
    </BrandModal>
  );
}
