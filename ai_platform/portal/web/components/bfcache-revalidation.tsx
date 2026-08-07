"use client";

import { useEffect } from "react";

function isBackForwardNavigation(): boolean {
  const navigation = performance.getEntriesByType("navigation")[0] as
    | PerformanceNavigationTiming
    | undefined;
  return navigation?.type === "back_forward";
}

/**
 * Protected Portal documents must never be trusted after browser-history
 * restoration. BFCache keeps the original page and its listeners alive, while
 * a non-BFCache back/forward load can mount React only after `pageshow` fired.
 * Cover both cases and force exactly one network reload so the Proxy re-checks
 * the current session and tenant boundary. The reload itself has navigation
 * type `reload`, so this does not form a loop.
 */
export function BfcacheRevalidation() {
  useEffect(() => {
    if (isBackForwardNavigation()) {
      window.location.reload();
      return;
    }

    const revalidateHistoryRestore = (event: PageTransitionEvent) => {
      if (event.persisted || isBackForwardNavigation()) window.location.reload();
    };

    window.addEventListener("pageshow", revalidateHistoryRestore);
    return () => window.removeEventListener("pageshow", revalidateHistoryRestore);
  }, []);

  return null;
}
