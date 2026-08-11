"use client";

import { usePathname } from "next/navigation";

import availability from "@/lib/product-surface-availability.json";

export function SurfaceAvailabilityNotice() {
  const pathname = usePathname();
  const surface = availability.surfaces.find((candidate) => candidate.route === pathname);

  if (!surface) return null;

  return (
    <div
      className="status-banner status-warning"
      role="note"
      aria-label={`${surface.label} capability availability`}
      data-surface-availability={surface.status}
    >
      <strong>{surface.label} capability unavailable</strong>
      <span>
        This surface is not connected end to end in the canonical product runtime. {surface.reason}
      </span>
      <span>Tracking: {surface.issues}</span>
    </div>
  );
}
