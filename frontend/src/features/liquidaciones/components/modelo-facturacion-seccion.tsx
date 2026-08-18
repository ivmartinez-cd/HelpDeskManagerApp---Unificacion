import type { Incidente } from "../types/liquidaciones";
import { formatARS } from "../lib/format";

interface Renglon {
  cant: number;
  totalServ: number;
  unitServ: number;
  kmCant: number;
  kmTotal: number;
  kmUnit: number;
}

function calcularRenglon(items: Incidente[]): Renglon {
  const cant = items.length;
  const totalServ = items.reduce((acc, i) => acc + i.costoServicioCobrado, 0);
  const kmCant = items.reduce((acc, i) => acc + i.cantKmCobrado, 0);
  const kmTotal = items.reduce(
    (acc, i) => acc + (i.costoTotalCobrado - i.costoServicioCobrado),
    0,
  );
  return {
    cant,
    totalServ,
    unitServ: cant > 0 ? totalServ / cant : 0,
    kmCant,
    kmTotal,
    kmUnit: kmCant > 0 ? kmTotal / kmCant : 0,
  };
}

const tdItem = "px-4 py-2.5 text-center font-heading font-bold text-foreground";
const tdDesc = "px-4 py-2.5 font-body font-bold uppercase text-foreground";
const tdSub = "px-4 py-2.5 pl-8 font-body text-muted-foreground";
const tdNum = "px-4 py-2.5 text-center font-body text-sm";
const tdMoney = "px-4 py-2.5 text-right font-body text-sm";

function FilaConcepto({ item, renglon }: { item: string; renglon: Renglon }) {
  return (
    <>
      <tr className="border-t border-border">
        <td className={tdItem}>{item}</td>
        <td className={tdDesc}>{item === "1" ? "Correctivos" : "Preventivos"}</td>
        <td className={`${tdNum} font-semibold`}>{renglon.cant}</td>
        <td className={tdMoney}>{formatARS(renglon.unitServ)}</td>
        <td className={`${tdMoney} font-bold text-foreground`}>{formatARS(renglon.totalServ)}</td>
      </tr>
      {renglon.kmCant > 0 && (
        <tr>
          <td className={tdItem} />
          <td className={tdSub}>viático</td>
          <td className={tdNum}>{renglon.kmCant}</td>
          <td className={tdMoney}>{formatARS(renglon.kmUnit)}</td>
          <td className={`${tdMoney} font-semibold text-foreground`}>{formatARS(renglon.kmTotal)}</td>
        </tr>
      )}
    </>
  );
}

export function ModeloFacturacionSeccion({
  incidentes,
  totalImporte,
}: {
  incidentes: Incidente[];
  totalImporte: number;
}) {
  const correctivos = incidentes.filter((i) => i.tipo.toLowerCase() !== "preventivo");
  const preventivos = incidentes.filter((i) => i.tipo.toLowerCase() === "preventivo");
  if (correctivos.length === 0 && preventivos.length === 0) return null;

  const renglonCorrectivos = calcularRenglon(correctivos);
  const renglonPreventivos = calcularRenglon(preventivos);

  return (
    <div className="rounded-[12px] border border-border bg-card overflow-hidden">
      <div className="border-b border-border px-5 py-3">
        <h2 className="font-heading text-base font-bold text-foreground">Modelo de facturación</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-border font-body text-[11px] font-bold uppercase tracking-[.06em] text-muted-foreground">
              <th className="w-16 px-4 py-2.5 text-center">Item</th>
              <th className="px-4 py-2.5">Descripción</th>
              <th className="w-24 px-4 py-2.5 text-center">Cant</th>
              <th className="w-32 px-4 py-2.5 text-right">$ Unit</th>
              <th className="w-32 px-4 py-2.5 text-right">Total</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {correctivos.length > 0 && <FilaConcepto item="1" renglon={renglonCorrectivos} />}
            {preventivos.length > 0 && <FilaConcepto item="2" renglon={renglonPreventivos} />}
          </tbody>
          <tfoot className="border-t border-border bg-muted/40">
            <tr>
              <td colSpan={4} className="px-4 py-3 text-right font-body text-xs font-bold uppercase tracking-[.06em] text-muted-foreground">
                Total general
              </td>
              <td className="px-4 py-3 text-right font-heading text-base font-extrabold text-brand-orange">
                {formatARS(totalImporte)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
