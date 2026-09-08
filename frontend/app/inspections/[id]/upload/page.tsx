"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { StatusBadge } from "@/components/badges";
import { api, ApiError } from "@/lib/api";
import { InspectionDetail } from "@/lib/types";

export default function UploadPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [insp, setInsp] = useState<InspectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [typ, setTyp] = useState("label");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .getInspection(Number(id))
      .then(setInsp)
      .catch((e) =>
        setError(e instanceof ApiError ? e.message : "Load failed")
      );
  }, [id]);

  async function doUpload() {
    if (files.length === 0) return;
    setBusy(true);
    setError(null);
    setWarnings([]);
    try {
      const res = await api.uploadImages(Number(id), files, typ);
      setFiles([]);
      setWarnings(res.warnings);
      const fresh = await api.getInspection(Number(id));
      setInsp(fresh);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function startProcessing() {
    setBusy(true);
    try {
      const res = await api.startProcessing(Number(id));
      router.push(`/inspections/${res.inspection_id}/processing`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Start failed");
      setBusy(false);
    }
  }

  return (
    <AuthShell>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-neutral-900">
              {insp?.public_id ?? "Inspection"}
            </h1>
            {insp && <StatusBadge status={insp.status} />}
          </div>
          <p className="text-sm text-neutral-500">
            Upload product-label images. Quality is checked automatically at
            capture.
          </p>
        </div>
        <Link
          href="/inspections"
          className="text-sm text-neutral-600 hover:underline"
        >
          ← Back
        </Link>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-neutral-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Add images
          </h2>
          <div className="mb-3">
            <label className="mb-1 block text-xs font-medium text-neutral-600">
              Sub-category
            </label>
            <select
              value={typ}
              onChange={(e) => setTyp(e.target.value)}
              className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm outline-none"
            >
              <option value="label">Label / front panel</option>
              <option value="nutrition">Nutrition / detail panel</option>
              <option value="package">Package / container</option>
              <option value="other">Other</option>
            </select>
          </div>
          <input
            type="file"
            multiple
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
            className="mb-3 block w-full text-sm text-neutral-600 file:mr-3 file:rounded-md file:border-0 file:bg-neutral-900 file:px-4 file:py-2 file:text-xs file:font-semibold file:text-white hover:file:bg-neutral-700"
          />
          {files.length > 0 && (
            <div className="mb-3 text-xs text-neutral-600">
              {files.length} file(s) selected.
            </div>
          )}
          <button
            onClick={doUpload}
            disabled={busy || files.length === 0}
            className="rounded-md bg-neutral-900 px-4 py-2 text-sm font-semibold text-white hover:bg-neutral-700 disabled:opacity-50"
          >
            {busy ? "Uploading…" : "Upload"}
          </button>

          {warnings.length > 0 && (
            <div className="mt-4 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              <div className="mb-1 font-semibold">Quality warnings</div>
              <ul className="list-inside list-disc space-y-0.5">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-neutral-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Uploaded images ({insp?.images.length ?? 0})
          </h2>
          {insp && insp.images.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No images yet. Upload at least one to continue.
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-2">
              {insp?.images.map((img) => (
                <div
                  key={img.id}
                  className="rounded-md border border-neutral-200 p-1"
                >
                  <div className="flex h-20 items-center justify-center rounded bg-neutral-100 text-[11px] text-neutral-500">
                    {img.type}
                  </div>
                  <div className="mt-1 truncate px-1 text-[11px] text-neutral-600">
                    {img.width}×{img.height}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={startProcessing}
          disabled={busy || !insp || insp.images.length === 0 || insp.status !== "draft"}
          className="rounded-md bg-emerald-600 px-5 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          Start OCR processing →
        </button>
        {insp && insp.status === "processing" && (
          <Link
            href={`/inspections/${insp.id}/processing`}
            className="text-sm font-medium text-neutral-900 underline underline-offset-2"
          >
            Processing in progress — view
          </Link>
        )}
      </div>
    </AuthShell>
  );
}