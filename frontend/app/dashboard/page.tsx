"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthShell } from "@/components/AuthShell";
import { api, ApiError } from "@/lib/api";
import { titleCase } from "@/lib/format";
import { DashboardData } from "@/lib/types";

function KpiCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-neutral-200 bg-white p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-neutral-500">
        {label}
      </div>
      <div className="mt-1 text-3xl font-bold text-neutral-900">{value}</div>
      {hint && <div className="mt-1 text-xs text-neutral-500">{hint}</div>}
    </div>
  );
}

function Bar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max === 0 ? 0 : Math.round((value / max) * 100);
  return (
    <div>
      <div className="flex justify-between text-xs text-neutral-600">
        <span>{label}</span>
        <span className="font-medium">{value}</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-neutral-200">
        <div
          className={`h-2 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getDashboard()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Load failed"));
  }, []);

  if (error) {
    return (
      <AuthShell>
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load dashboard: {error}
        </div>
      </AuthShell>
    );
  }

  if (!data) {
    return (
      <AuthShell>
        <div className="text-sm text-neutral-500">Loading dashboard…</div>
      </AuthShell>
    );
  }

  const statusOrder = [
    "draft",
    "processing",
    "ready_for_review",
    "reviewed",
    "closed",
  ] as const;
  const maxStatus = Math.max(1, ...statusOrder.map((s) => data.status_breakdown[s] ?? 0));
  const maxAssess = Math.max(
    1,
    ...Object.values(data.assessment_breakdown).map(Number)
  );

  return (
    <AuthShell>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-neutral-900">Dashboard</h1>
        <p className="text-sm text-neutral-500">
          Evidence-backed compliance overview
        </p>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-5">
        <KpiCard label="Inspections" value={data.total_inspections} />
        <KpiCard
          label="Ready for review"
          value={data.status_breakdown.ready_for_review ?? 0}
        />
        <KpiCard
          label="Pending review"
          value={data.findings.pending_review}
          hint="automated findings"
        />
        <KpiCard
          label="Flagged"
          value={data.findings.flagged_potential}
          hint="potential non-compliance"
        />
        <KpiCard
          label="Created this month"
          value={data.created_this_month}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-xl border border-neutral-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Inspection status
          </h2>
          <div className="space-y-3">
            {statusOrder.map((s) => (
              <Bar
                key={s}
                label={titleCase(s)}
                value={data.status_breakdown[s] ?? 0}
                max={maxStatus}
                color="bg-neutral-900"
              />
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-neutral-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Assessment outcomes
          </h2>
          <div className="space-y-3">
            {(Object.entries(data.assessment_breakdown) as [string, number][]).map(
              ([k, v]) => (
                <Bar
                  key={k}
                  label={titleCase(k)}
                  value={v}
                  max={maxAssess}
                  color={
                    k === "PASS"
                      ? "bg-emerald-500"
                      : k === "POTENTIAL NON-COMPLIANCE"
                        ? "bg-red-500"
                        : k === "NEEDS VERIFICATION"
                          ? "bg-amber-500"
                          : "bg-neutral-400"
                  }
                />
              )
            )}
          </div>
        </div>

        <div className="rounded-xl border border-neutral-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Recent inspections
          </h2>
          <ul className="space-y-2">
            {Object.entries(data.channel_breakdown)
              .slice(0, 4)
              .map(([ch, count]) => (
                <li
                  key={ch}
                  className="flex justify-between rounded-md bg-neutral-50 px-3 py-2 text-sm"
                >
                  <span className="text-neutral-700">{titleCase(ch)}</span>
                  <span className="font-medium text-neutral-900">{count}</span>
                </li>
              ))}
          </ul>
          <Link
            href="/inspections"
            className="mt-3 inline-block text-sm font-medium text-neutral-900 underline underline-offset-2"
          >
            View all inspections →
          </Link>
        </div>
      </div>

      {data.status_breakdown.ready_for_review ? (
        <Link
          href="/inspections?status=ready_for_review"
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-neutral-900 px-4 py-2 text-sm font-semibold text-white hover:bg-neutral-700"
        >
          Review pending inspections →
        </Link>
      ) : null}
    </AuthShell>
  );
}