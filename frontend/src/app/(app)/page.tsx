import { Clock3 } from "lucide-react";

export const metadata = {
  title: "Inicio",
};

export default function HomePage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-20 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-[9px] bg-brand-orange/[0.12] text-brand-orange">
        <Clock3 className="h-6 w-6" />
      </span>
      <h1 className="font-heading text-2xl font-extrabold text-foreground">Próximamente</h1>
      <p className="max-w-sm font-body text-sm text-muted-foreground">
        El panel de Inicio se arma a medida que se migran los módulos de negocio. Por ahora,
        accedé a tus herramientas desde el menú lateral.
      </p>
    </div>
  );
}
