"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { StatusBadge } from "@/components/badges";
import { api, ApiError } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { InspectionListItem, InspectionStatus } from "@/lib/types";

const STATUS_FILTERS = [
  { value: "", label: "All statuses" },
  { value: "draft", label: "Draft" },
  { value: "processing", label: "Processing" },
  { value: "ready_for_review", label: "Ready for review" },
  { value: "reviewed", label: "Reviewed" },
  { value: "closed", label: "Closed" },
] as const;

export default function InspectionsPage() {
  return (
    <Suspense
      fallback={
        <AuthShell>
          <div className="text-sm text-neutral-500">Loading…</div>
        </AuthShell>
      }
    >
      <InspectionsView />
    </Suspense>
  );
}

function InspectionsView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [items, setItems] = useState<InspectionListItem[] | null>(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState(searchParams.get("q") ?? "");
  const [status, setStatus] = useState(
    searchParams.get("status") ?? ""
  );
  const [debouncedQ, setDebouncedQ] = useState(q);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q), 350);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    let cancelled = false;
    const params: Record<string, string> = {};
    if (debouncedQ.trim()) params.q = debouncedQ.trim();
    if (status) params.status = status;
    api
      .listInspections(params)
      .then((res) => {
        if (!cancelled) {
          setError(null);
          setItems(res.items);
          setTotal(res.total);
        }
      })
      .catch((e) => {
        if (!cancelled)
          setError(e instanceof ApiError ? e.message : "Load failed");
      });
    return () => {
      cancelled = true;
    };
  }, [debouncedQ, status]);

  return (
    <AuthShell>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">Inspections</h1>
          <p className="text-sm text-neutral-500">
            History and review queues ({total} total)
          </p>
        </div>
        <Link
          href="/inspections/new"
          className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-semibold text-white hover:bg-neutral-700"
        >
          New inspection
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search location, product, origin…"
          className="w-72 rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm outline-none focus:border-neutral-500"
        />
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm outline-none focus:border-neutral-500"
        >
          {STATUS_FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {!items ? (
        <div className="text-sm text-neutral-500">Loading…</div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-10 text-center text-sm text-neutral-500">
          No inspections match.
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-neutral-50 text-xs uppercase tracking-wide text-neutral-500">
              <tr>
                <th className="px-4 py-3 font-medium">ID</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Channel</th>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Images</th>
                <th className="px-4 py-3 font-medium">Findings</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {items.map((it) => (
                <tr
                  key={it.id}
                  onClick={() => router.push(`/inspections/${it.id}/assessment`)}
                  className="cursor-pointer transition-colors hover:bg-neutral-50"
                >
                  <td className="px-4 py-3 font-medium text-neutral-900">
                    {it.public_id}
                  </td>
                  <td className="px-4 py-3 text-neutral-700">{it.location}</td>
                  <td className="px-4 py-3 text-neutral-700">
                    {it.channel.toUpperCase()}
                  </td>
                  <td className="px-4 py-3 text-neutral-700">
                    {formatDate(it.inspection_date)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={it.status as InspectionStatus} />
                  </td>
                  <td className="px-4 py-3 text-neutral-700">{it.image_count}</td>
                  <td className="px-4 py-3 text-neutral-700">
                    {it.finding_count}
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