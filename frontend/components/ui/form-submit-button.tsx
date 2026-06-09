"use client";

import { useFormStatus } from "react-dom";
import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";

export function FormSubmitButton({
  children,
  disabled,
  className,
}: {
  children: ReactNode;
  disabled?: boolean;
  className?: string;
}) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={disabled || pending}
      className={className}
    >
      {pending ? <Loader2 className="size-3.5 animate-spin" /> : children}
    </button>
  );
}
