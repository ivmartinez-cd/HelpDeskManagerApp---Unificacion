import { LiquidacionDetalleView } from "@/features/liquidaciones/components/liquidacion-detalle";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function LiquidacionDetallePage({ params }: Props) {
  const { id } = await params;
  return <LiquidacionDetalleView id={id} />;
}
