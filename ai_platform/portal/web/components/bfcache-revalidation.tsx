"use client";

import { useEffect } from "react";

/**
 * Chromium may restore a protected Portal document from the back/forward cache
 * without consulting the server. Force a network revalidation only for BFCache
 * restores so the Proxy can re-check the current session and tenant boundary.
 */
export function BfcacheRevalidation() {
  useEffect(() => {
    const revalidatePersistedPage = (event: PageTransitionEvent) => {
      if (event.persisted) window.location.reload();
    };

    window.addEventListener("pageshow", revalidatePersistedPage);
    return () => window.removeEventListener("pageshow", revalidatePersistedPage);
  }, []);

  return null;
}
