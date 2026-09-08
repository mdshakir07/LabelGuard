"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode } from "react";
import { useAuth } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "▦" },
  { href: "/inspections", label: "Inspections", icon: "☰" },
  { href: "/inspections/new", label: "New inspection", icon: "＋" },
  { href: "/products", label: "Products", icon: "□" },
  { href: "/admin/rules", label: "Rules", icon: "⚖" },
];

const ROLE_LABEL: Record<string, string> = {
  inspector: "Inspector",
  reviewer: "Reviewer",
  admin: "Administrator",
  auditor: "Auditor",
};

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-neutral-100">
      <aside className="flex w-56 shrink-0 flex-col border-r border-neutral-200 bg-white">
        <div className="border-b border-neutral-200 px-4 py-4">
          <div className="text-sm font-bold tracking-tight text-neutral-900">
            MitraMetrology AI
          </div>
          <div className="mt-0.5 text-[11px] text-neutral-500">
            Scan. Verify. Explain. Enforce.
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => {
            const active =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors ${
                  active
                    ? "bg-neutral-900 text-white"
                    : "text-neutral-700 hover:bg-neutral-100"
                }`}
              >
                <span className="w-4 text-center">{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>
        {user && (
          <div className="border-t border-neutral-200 p-3">
            <div className="mb-1 px-1 text-xs text-neutral-700">
              <div className="font-semibold">{user.name}</div>
              <div className="text-neutral-500">
                {ROLE_LABEL[user.role] ?? user.role}
              </div>
            </div>
            <button
              onClick={() => {
                logout();
                router.push("/login");
              }}
              className="w-full rounded-md border border-neutral-300 px-3 py-1.5 text-xs text-neutral-700 hover:bg-neutral-100"
            >
              Sign out
            </button>
          </div>
        )}
      </aside>
      <main className="flex-1 overflow-x-auto p-6">{children}</main>
    </div>
  );
}