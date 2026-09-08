"use client";

import { useEffect, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { RuleListResponse } from "@/lib/types";

export default function RulesPage() {
  const [data, setData] = useState<RuleListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listRules()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Load failed"));
  }, []);

  return (
    <AuthShell>
      <div className="mb-5">
        <h1 className="text-xl font-bold text-neutral-900">Rules administration</h1>
        <p className="text-sm text-neutral-500">
          Versioned rules · currently{" "}
          <span className="font-mono">{data?.version ?? "—"}</span>
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!data ? (
        <div className="text-sm text-neutral-500">Loading…</div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-neutral-50 text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="px-4 py-3 font-medium">Rule ID</th>
                <th className="px-4 py-3 font-medium">Title</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Effective from</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {data.rules.map((r) => (
                <tr key={r.id} className="hover:bg-neutral-50">
                  <td className="px-4 py-2.5 font-mono text-xs font-semibold text-neutral-900">
                    {r.rule_id}
                  </td>
                  <td className="px-4 py-2.5 text-neutral-700">{r.title}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${
                        r.status === "published"
                          ? "border-emerald-300 bg-emerald-50 text-emerald-700"
                          : r.status === "draft"
                            ? "border-amber-300 bg-amber-50 text-amber-700"
                            : "border-neutral-300 bg-neutral-100 text-neutral-600"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-neutral-700">
                    {formatDate(r.effective_from)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AuthShell>
  );
}