import { type HTMLAttributes } from "react";
import { cn } from "@/shared/utils/cn";

export function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-xl bg-black/5 dark:bg-white/10", className)}
      {...props}
    />
  );
}
