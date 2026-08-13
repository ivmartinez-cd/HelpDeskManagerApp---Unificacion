import { CoberturasView } from "@/features/coberturas/components/coberturas-view";

export const metadata = {
  title: "Coberturas",
};

export default function CoberturasContadoresPage() {
  return <CoberturasView entityType="contador" />;
}
