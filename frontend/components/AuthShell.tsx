import { ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { AppShell } from "@/components/AppShell";

function Inner({ children }: { children: ReactNode }) {
  const { ready, user } = useAuth();
  if (!ready || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-100 text-sm text-neutral-500">
        Loading…
      </div>
    );
  }
  return <AppShell>{children}</AppShell>;
}

export function AuthShell({ children }: { children: ReactNode }) {
  return <Inner>{children}</Inner>;
}

export default AuthShell;