"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError, setToken } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const DEMO = [
  { email: "inspector@mitra.in", password: "inspector@123", label: "Inspector" },
  { email: "reviewer@mitra.in", password: "reviewer@123", label: "Reviewer" },
  { email: "admin@mitra.in", password: "admin@123", label: "Admin" },
  { email: "auditor@mitra.in", password: "auditor@123", label: "Auditor" },
];

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await api.login(email.trim(), password);
      setToken(res.access_token);
      setUser(res.user);
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-neutral-950 p-8">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <div className="text-xl font-bold text-white">MitraMetrology AI</div>
          <div className="mt-1 text-xs uppercase tracking-widest text-neutral-400">
            Scan · Verify · Explain · Enforce
          </div>
        </div>
        <form
          onSubmit={submit}
          className="rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-xl"
        >
          <label className="mb-1 block text-xs font-medium text-neutral-300">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="username"
            className="mb-3 w-full rounded-md border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none focus:border-neutral-500"
          />
          <label className="mb-1 block text-xs font-medium text-neutral-300">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="mb-4 w-full rounded-md border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none focus:border-neutral-500"
          />
          {error && (
            <div className="mb-3 rounded-md border border-red-800 bg-red-950 px-3 py-2 text-xs text-red-300">
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-md bg-white px-3 py-2 text-sm font-semibold text-neutral-900 hover:bg-neutral-200 disabled:opacity-60"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="mt-4 rounded-lg border border-neutral-800 bg-neutral-900/60 p-3">
          <div className="mb-2 text-[11px] uppercase tracking-wide text-neutral-500">
            Demo accounts
          </div>
          <div className="space-y-1">
            {DEMO.map((d) => (
              <button
                key={d.email}
                type="button"
                onClick={() => {
                  setEmail(d.email);
                  setPassword(d.password);
                }}
                className="flex w-full items-center justify-between rounded px-2 py-1 text-left text-xs text-neutral-400 hover:bg-neutral-800"
              >
                <span>{d.label}</span>
                <span className="text-neutral-600">{d.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}