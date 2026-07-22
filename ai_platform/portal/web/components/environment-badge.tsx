import type { PortalEnvironment } from "@/lib/contracts";

export function EnvironmentBadge({ environment }: { environment: PortalEnvironment }) {
  return (
    <span className={`environment-badge environment-${environment}`} data-testid="environment-badge">
      {environment.toUpperCase()}
    </span>
  );
}
