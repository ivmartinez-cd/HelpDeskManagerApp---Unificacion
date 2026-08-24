"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { BrandInput, BrandSelect } from "@/shared/components/ui/brand-form";
import { Spinner } from "@/shared/components/ui/spinner";
import { liquidacionesApi } from "@/features/liquidaciones/api/liquidaciones-api";
import type { PrestadorLiquidacion, SigesEmpresa } from "@/features/liquidaciones/types/liquidaciones";
import { prestadoresApi } from "@/features/prestadores/api/prestadores-api";
import type { OperadorOption } from "@/features/prestadores/types/prestadores";
import { PasoAcciones } from "./alta-prestador-wizard-ui";

const SIN_ASIGNAR = "__sin_asignar__";

export function PasoCanalDirecto({
  prestador,
  onVinculado,
  onSaltear,
}: {
  prestador: PrestadorLiquidacion;
  onVinculado: () => void;
  onSaltear: () => void;
}) {
  const [valor, setValor] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirmar = async () => {
    const cdPrestadorId = valor.trim() === "" ? null : Number(valor);
    if (cdPrestadorId !== null && (!Number.isInteger(cdPrestadorId) || cdPrestadorId <= 0)) {
      setError("Tiene que ser un número entero positivo");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await liquidacionesApi.vincularCdPrestador(prestador.id, cdPrestadorId);
      toast.success("Vínculo a Canal Directo guardado");
      onVinculado();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Id numérico del prestador en Canal Directo/AyC. Sin este vínculo, el sync
        de liquidaciones nunca lo consulta contra wsAyC — sus liquidaciones no
        entran a la app.
      </p>
      <BrandInput
        label="Id en Canal Directo"
        type="number"
        min={1}
        step={1}
        placeholder="Ej: 123"
        value={valor}
        onChange={(e) => setValor(e.target.value)}
      />
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      <PasoAcciones onSaltear={onSaltear} primario={confirmar} primarioTexto="Vincular y continuar →" saving={saving} />
    </div>
  );
}

export function PasoSla({
  prestador,
  sigesElegida,
  onCreado,
  onSaltear,
}: {
  prestador: PrestadorLiquidacion;
  sigesElegida: SigesEmpresa | null;
  onCreado: () => void;
  onSaltear: () => void;
}) {
  const [operadores, setOperadores] = useState<OperadorOption[] | null>(null);
  const [denComercial, setDenComercial] = useState(sigesElegida?.denComercial ?? "");
  const [razonSocial, setRazonSocial] = useState(sigesElegida?.razonSocial ?? "");
  const [cuit, setCuit] = useState(prestador.cuit ?? "");
  const [operadorId, setOperadorId] = useState(SIN_ASIGNAR);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sigesElegida) return;
    prestadoresApi
      .listOperadores()
      .then(setOperadores)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error al cargar operadores"));
  }, [sigesElegida]);

  if (!sigesElegida) {
    return (
      <div className="flex flex-col gap-4">
        <p className="font-body text-sm text-muted-foreground">
          El alta en el módulo SLA necesita el vínculo Siges — sin él no hay forma
          de asociar este prestador al catálogo de asignación de operador. Podés
          saltear y darlo de alta ahí más tarde.
        </p>
        <PasoAcciones onSaltear={onSaltear} />
      </div>
    );
  }

  const confirmar = async () => {
    setSaving(true);
    setError(null);
    try {
      await prestadoresApi.createPrestador({
        sigesEmpresaId: sigesElegida.sigesEmpresaId,
        denComercial,
        razonSocial: razonSocial || null,
        cuit: cuit || null,
        operadorId: operadorId === SIN_ASIGNAR ? null : operadorId,
      });
      toast.success("Alta en el módulo SLA creada");
      onCreado();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Error al dar de alta en SLA");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <p className="font-body text-sm text-muted-foreground">
        Alta en el módulo de asignación de operador/SLA — catálogo independiente
        del de Liquidaciones, vinculado por el mismo id de Siges (#{sigesElegida.sigesEmpresaId}).
      </p>
      <BrandInput label="Denominación comercial" required value={denComercial} onChange={(e) => setDenComercial(e.target.value)} />
      <BrandInput label="Razón social" value={razonSocial} onChange={(e) => setRazonSocial(e.target.value)} />
      <BrandInput label="CUIT" value={cuit} onChange={(e) => setCuit(e.target.value)} />
      {operadores === null ? (
        <div className="flex h-10 items-center"><Spinner /></div>
      ) : (
        <BrandSelect label="Operador" value={operadorId} onChange={(e) => setOperadorId(e.target.value)}>
          <option value={SIN_ASIGNAR}>Sin asignar</option>
          {operadores.map((op) => (
            <option key={op.id} value={op.id}>{op.fullName}</option>
          ))}
        </BrandSelect>
      )}
      {error && <p className="font-body text-sm text-destructive">{error}</p>}
      <PasoAcciones
        onSaltear={onSaltear}
        primario={confirmar}
        primarioTexto="Dar de alta y terminar"
        primarioDisabled={!denComercial}
        saving={saving}
      />
    </div>
  );
}
