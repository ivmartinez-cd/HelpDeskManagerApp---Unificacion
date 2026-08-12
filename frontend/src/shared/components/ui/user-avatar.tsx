import { cn } from "@/shared/utils/cn";

/** Avatar circular con las iniciales de un usuario y su color real de
 * Gestión (`AppUser.color`, ver ADR-009) de fondo — mismo bloque que ya
 * pintaba `sidebar.tsx` para el usuario logueado, promovido acá para
 * reusarlo donde haga falta un avatar de operador (ej. Prestadores). */

export function getInitials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

const SIZE_CLASSES = {
  sm: "h-[26px] w-[26px] text-[11px]",
  md: "h-[34px] w-[34px] text-[13px]",
  lg: "h-[44px] w-[44px] text-base",
} as const;

interface UserAvatarProps {
  fullName: string;
  color?: string | null;
  size?: keyof typeof SIZE_CLASSES;
  className?: string;
}

export function UserAvatar({ fullName, color, size = "md", className }: UserAvatarProps) {
  return (
    <span
      style={color ? { backgroundColor: color } : undefined}
      className={cn(
        "flex flex-none items-center justify-center rounded-full font-heading font-bold text-white",
        SIZE_CLASSES[size],
        !color && "bg-brand-gray",
        className,
      )}
    >
      {getInitials(fullName)}
    </span>
  );
}
