import { FichaPersonaView } from "@/features/personas/components/ficha/ficha-persona-view";

export const metadata = {
  title: "Persona",
};

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function FichaPersonaPage({ params }: PageProps) {
  const { id } = await params;
  return <FichaPersonaView id={id} />;
}
