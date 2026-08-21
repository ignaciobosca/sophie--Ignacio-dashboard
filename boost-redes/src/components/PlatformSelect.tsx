"use client";

import { useEffect, useRef, useState } from "react";
import type { Platform } from "@/lib/types";
import { PLATFORMS } from "@/lib/types";
import { PlatformIcon } from "./icons";

export default function PlatformSelect({
  value,
  onChange,
}: {
  value: Platform;
  onChange: (p: Platform) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const current = PLATFORMS.find((p) => p.id === value) ?? PLATFORMS[0];

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none focus:border-brand"
      >
        <PlatformIcon platform={current.id} brand className="h-4 w-4 shrink-0" />
        <span className="flex-1 truncate text-left">{current.label}</span>
        <span className={`text-white/40 transition-transform ${open ? "rotate-180" : ""}`}>▾</span>
      </button>

      {open && (
        <div className="absolute z-10 mt-2 max-h-64 w-full overflow-auto rounded-xl border border-white/10 bg-panel p-1 shadow-glow">
          {PLATFORMS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => {
                onChange(p.id);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition hover:bg-white/10 ${
                p.id === value ? "bg-white/5" : ""
              }`}
            >
              <PlatformIcon platform={p.id} brand className="h-4 w-4 shrink-0" />
              <span className="flex-1 truncate">{p.label}</span>
              {p.id === value && <span className="text-brand-glow">✓</span>}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
