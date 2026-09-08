"use client";

import { useEffect, useState } from "react";
import { use } from "react";
import Link from "next/link";
import { AuthShell } from "@/components/AuthShell";
import { StatusBadge } from "@/components/badges";
import { api, ApiError } from "@/lib/api";
import { InspectionDetail } from "@/lib/types";

export default function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [insp, setInsp] = useState<InspectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api
      .getInspection(Number(id))
      .then(setInsp)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Load failed"));
  }, [id]);

  async function download(format: "pdf" | "docx") {
    setBusy(format);
    try {
      await api.downloadReport(Number(id), format);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Download failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <AuthShell>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-neutral-900">
              {insp?.public_id ?? "Report"}
            </h1>
            {insp && <StatusBadge status={insp.status} />}
          </div>
          <p className="text-sm text-neutral-500">
            PDF / DOCX compliance report with evidence links
          </p>
        </div>
        <Link
          href={`/inspections/${id}/assessment`}
          className="text-sm text-neutral-600 hover:underline"
        >
          ← Back to assessment
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <button
          onClick={() => download("pdf")}
          disabled={busy !== null}
          className="rounded-xl border border-neutral-200 bg-white p-6 text-left transition-colors hover:border-neutral-400 disabled:opacity-60"
        >
          <div className="text-lg font-bold text-neutral-900">
            {busy === "pdf" ? "Preparing…" : "PDF report"}
          </div>
          <p className="mt-1 text-sm text-neutral-500">
            Print-ready document annotated with bboxes, OCR spans, rule
            version and reviewer remarks.
          </p>
        </button>
        <button
          onClick={() => download("docx")}
          disabled={busy !== null}
          className="rounded-xl border border-neutral-200 bg-white p-6 text-left transition-colors hover:border-neutral-400 disabled:opacity-60"
        >
          <div className="text-lg font-bold text-neutral-900">
            {busy === "docx" ? "Preparing…" : "DOCX report"}
          </div>
          <p className="mt-1 text-sm text-neutral-500">
            Editable document for official submission and further review.
          </p>
        </button>
      </div>

      {insp && (
        <div className="mt-6 rounded-xl border border-neutral-200 bg-white p-4 text-xs text-neutral-500">
          <div className="mb-1 font-semibold text-neutral-700">
            Report meta
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
            <span>Inspector: #{insp.inspector_id}</span>
            <span>Location: {insp.location}</span>
            <span>Channel: {insp.channel}</span>
            <span>Ruleset: {insp.ruleset_version ?? "—"}</span>
            <span>Fields: {insp.fields.length}</span>
            <span>Assessments: {insp.assessments.length}</span>
          </div>
        </div>
      )}
    </AuthShell>
  );
}