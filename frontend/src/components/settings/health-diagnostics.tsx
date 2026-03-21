"use client";

import { useState } from "react";
import { useAuth } from "@/context/auth-context";
import { getDiagnostics } from "@/lib/diagnostics-api";
import type { ServiceStatus } from "@/lib/diagnostics-api";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw } from "lucide-react";

function StatusDot({ status }: { status: string }) {
  const color =
    status === "ok"
      ? "bg-green-500"
      : status === "error"
        ? "bg-red-500"
        : "bg-gray-400";
  return <span className={`inline-block h-3 w-3 rounded-full ${color}`} />;
}

export function HealthDiagnostics() {
  const { token } = useAuth();
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);

  const handleCheck = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await getDiagnostics(token);
      setServices(data.services);
      setChecked(true);
    } catch {
      // Error handled
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-muted-foreground text-sm">
          Check the status of all configured integrations.
        </p>
        <Button
          onClick={() => void handleCheck()}
          disabled={loading}
          variant="outline"
          size="sm"
        >
          {loading ? (
            <>
              <Loader2 className="mr-1 h-4 w-4 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <RefreshCw className="mr-1 h-4 w-4" />
              Check Now
            </>
          )}
        </Button>
      </div>

      {checked && services.length > 0 && (
        <div className="space-y-2">
          {services.map((svc, i) => (
            <div
              key={`${svc.name}-${i}`}
              className="bg-card flex items-center justify-between rounded-lg border p-3"
            >
              <div className="flex items-center gap-3">
                <StatusDot status={svc.status} />
                <div>
                  <p className="text-sm font-medium">{svc.name}</p>
                  {svc.error && (
                    <p className="text-destructive text-xs">{svc.error}</p>
                  )}
                </div>
              </div>
              <div className="text-muted-foreground text-xs">
                {svc.status === "ok" && svc.latency_ms != null
                  ? `${svc.latency_ms}ms`
                  : svc.status === "unconfigured"
                    ? "Not configured"
                    : svc.status === "error"
                      ? "Error"
                      : ""}
              </div>
            </div>
          ))}
        </div>
      )}

      {checked && services.length === 0 && (
        <p className="text-muted-foreground text-sm">
          No services configured yet.
        </p>
      )}
    </div>
  );
}
