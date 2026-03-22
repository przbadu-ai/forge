"use client";

import { useEffect } from "react";

export function ServiceWorkerRegister() {
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      // Skip SW registration when behind a reverse proxy (production domain).
      // The SW interferes with Next.js rewrites that proxy /api/* to the backend.
      // SW will be re-enabled after Phase 13 (Install UX) adds proper SW/proxy integration.
      const isProxied = !window.location.port || window.location.port === "443" || window.location.port === "80";
      if (isProxied) {
        // Unregister any existing SW to clean up
        navigator.serviceWorker.getRegistrations().then((regs) => {
          regs.forEach((r) => r.unregister());
        });
        return;
      }

      navigator.serviceWorker.register("/sw.js", {
        scope: "/",
        updateViaCache: "none",
      });
    }
  }, []);

  return null;
}
