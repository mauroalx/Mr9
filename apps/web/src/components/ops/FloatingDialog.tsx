"use client";

import { useEffect, useRef } from "react";
import {
  floatingDialogStyle,
  type FloatingDialogPosition,
} from "@/lib/floating-dialog";

type FloatingDialogProps = {
  children: React.ReactNode;
  labelledBy: string;
  onClose: () => void;
  position: FloatingDialogPosition;
  width: number;
};

export function FloatingDialog({
  children,
  labelledBy,
  onClose,
  position,
  width,
}: FloatingDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null;
    const firstControl = dialogRef.current?.querySelector<HTMLElement>(
      "button, input, select, textarea, [tabindex]:not([tabindex='-1'])",
    );
    firstControl?.focus();
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") onCloseRef.current();
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      previousFocus?.focus();
    };
  }, []);

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        className="absolute inset-0 bg-transparent"
        aria-label="Fechar"
        onClick={onClose}
      />
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="false"
        aria-labelledby={labelledBy}
        style={floatingDialogStyle(position, width)}
        className="fixed z-10 flex flex-col overflow-hidden rounded-[8px] border border-rule bg-panel shadow-xl"
      >
        {children}
      </div>
    </div>
  );
}
