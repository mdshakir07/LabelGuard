"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { use } from "react";
import { AuthShell } from "@/components/AuthShell";
import {
  ReviewBadge,
  ResultBadge,
  StatusBadge,
  severityColor,
} from "@/components/badges";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cx, formatDateTime } from "@/lib/format";
import { CategorySuggestion, ExtractedField, Finding, InspectionDetail } from "@/lib/types";

interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export default function AssessmentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const { user } = useAuth();
  const canReview = user?.role === "reviewer" || user?.role === "admin";
  const [insp, setInsp] = useState<InspectionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [imageUrls, setImageUrls] = useState<Record<number, string>>({});
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [selectedImageId, setSelectedImageId] = useState<number | null>(null);
  const [editingField, setEditingField] = useState<ExtractedField | null>(null);
  const [fieldDraft, setFieldDraft] = useState("");
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [category, setCategory] = useState<CategorySuggestion | null>(null);
  const [categoryInput, setCategoryInput] = useState("");

  useEffect(() => {
    api
      .getInspection(Number(id))
      .then((d) => {
        setInsp(d);
        setCategoryInput(d.category ?? "");
        if (d.images.length > 0) setSelectedImageId(d.images[0].id);
      })
      .catch((e) => setError(e instanceof ApiError ? e.message : "Load failed"));
    api
      .getCategorySuggestion(Number(id))
      .then(setCategory)
      .catch(() => setCategory(null));
  }, [id]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!selectedImageId) return;
      if (imageUrls[selectedImageId]) return;
      try {
        const url = await api.fetchImageUrl(Number(id), selectedImageId);
        if (!cancelled) {
          setImageUrls((m) => ({ ...m, [selectedImageId]: url }));
        }
      } catch {
        // image may not exist yet
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, selectedImageId, imageUrls]);

  const selectedBbox = useMemo<BBox | null>(() => {
    const f = selectedFinding;
    if (!f?.bbox) return null;
    return f.bbox as BBox;
  }, [selectedFinding]);

  const selectedImage = insp?.images.find((i) => i.id === selectedImageId) ?? null;

  function showToast(msg: string) {
    setToast(msg);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3500);
  }

  async function patchFinding(f: Finding, status: string) {
    setBusy(true);
    try {
      await api.reviewFinding(f.id, status, comment);
      showToast(`Finding ${f.rule_id} marked ${status}`);
      setComment("");
      const d = await api.getInspection(Number(id));
      setInsp(d);
      const updated = d.assessments
        .flatMap((a) => a.findings)
        .find((x) => x.id === f.id);
      setSelectedFinding(updated ?? null);
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveFieldEdit() {
    if (!editingField) return;
    setBusy(true);
    try {
      await api.editField(Number(id), editingField.id, fieldDraft);
      const d = await api.getInspection(Number(id));
      setInsp(d);
      setEditingField(null);
      showToast("Field corrected — re-running rule assessment…");
      await api.reAssess(Number(id));
      showToast("Re-assessment queued. Refresh to see updated findings.");
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveCategory() {
    const value = categoryInput.trim();
    if (!value) return;
    setBusy(true);
    try {
      await api.setCategory(Number(id), value);
      showToast(`Category set to "${value}" — re-running assessment…`);
      await api.reAssess(Number(id));
      showToast("Re-assessment queued. Refresh to see updated findings.");
      const d = await api.getInspection(Number(id)).catch(() => null);
      if (d) setInsp(d);
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : "Category save failed");
    } finally {
      setBusy(false);
    }
  }

  async function finalize(action: "review" | "close") {
    setBusy(true);
    try {
      const d =
        action === "review"
          ? await api.reviewInspection(Number(id))
          : await api.closeInspection(Number(id));
      setInsp(d);
      showToast(
        action === "review"
          ? "Inspection marked REVIEWED — all findings have decisions."
          : "Inspection CLOSED. Fields are now locked."
      );
    } catch (e) {
      showToast(e instanceof ApiError ? e.message : "Finalize failed");
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <AuthShell>
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      </AuthShell>
    );
  }

  if (!insp) {
    return (
      <AuthShell>
        <div className="text-sm text-neutral-500">Loading inspection…</div>
      </AuthShell>
    );
  }

  const allFindings = insp.assessments.flatMap((a) => a.findings);
  const pendingCount = allFindings.filter((f) => f.review_status === "pending").length;

  return (
    <AuthShell>
      {toast && (
        <div className="fixed right-4 top-4 z-50 rounded-md border border-neutral-300 bg-neutral-900 px-4 py-2 text-xs font-medium text-white shadow-lg">
          {toast}
        </div>
      )}

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-neutral-900">
              {insp.public_id}
            </h1>
            <StatusBadge status={insp.status} />
          </div>
          <p className="text-sm text-neutral-500">
            {insp.location} · {insp.channel} · ruleset {insp.ruleset_version ?? "—"}
          </p>
        </div>
        <div className="flex gap-2 text-sm">
          <button
            onClick={() => window.location.reload()}
            className="rounded-md border border-neutral-300 bg-white px-3 py-2 text-neutral-700 hover:bg-neutral-100"
          >
            Refresh
          </button>
          <button
            onClick={async () => {
              try {
                await api.generateReport(Number(id), "pdf");
                showToast("Report generating…");
              } catch (e) {
                showToast(e instanceof ApiError ? e.message : "Report failed");
              }
            }}
            className="rounded-md bg-neutral-900 px-4 py-2 font-semibold text-white hover:bg-neutral-700"
          >
            Generate report
          </button>
        </div>
      </div>

      {pendingCount > 0 && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-2 text-xs font-medium text-amber-800">
          {pendingCount} automated finding(s) await human review. Automated
          results are never a legal conclusion.
        </div>
      )}

      <div className="mb-4 grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-neutral-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-neutral-900">
            Commodity category (P0 confirmation)
          </h2>
          <p className="mb-3 text-xs text-neutral-500">
            Applicability runs against this value. Confirming re-runs the rule
            assessment under the confirmed category.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              value={categoryInput}
              onChange={(e) => setCategoryInput(e.target.value)}
              className="w-40 rounded-md border border-neutral-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-neutral-500"
              placeholder="e.g. food"
            />
            <button
              onClick={saveCategory}
              disabled={busy || !categoryInput.trim() || insp.status === "closed"}
              className="rounded-md bg-neutral-900 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
            >
              Save & re-assess
            </button>
            {category?.suggestions.map((s) => (
              <button
                key={s.category}
                onClick={() => setCategoryInput(s.category)}
                className="rounded-full border border-neutral-300 bg-neutral-50 px-2.5 py-1 text-xs text-neutral-700 hover:border-neutral-500"
                title={s.basis}
              >
                {s.category} · {Math.round(s.confidence * 100)}%
              </button>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-neutral-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-neutral-900">
            Review & finalize
          </h2>
          <p className="mb-3 text-xs text-neutral-500">
            Automated findings must each get a human decision before the
            inspection can be marked reviewed; closing locks the record.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {canReview && (
              <>
                <button
                  onClick={() => finalize("review")}
                  disabled={
                    busy || pendingCount > 0 || insp.status !== "ready_for_review"
                  }
                  className="rounded-md bg-violet-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                >
                  Mark reviewed
                </button>
                <button
                  onClick={() => finalize("close")}
                  disabled={
                    busy ||
                    pendingCount > 0 ||
                    !["ready_for_review", "reviewed"].includes(insp.status)
                  }
                  className="rounded-md bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                >
                  Close inspection
                </button>
              </>
            )}
            {!canReview && (
              <span className="text-xs text-neutral-500">
                Reviewer/admin only — findings review is the human gate.
              </span>
            )}
            {pendingCount > 0 && (
              <span className="text-xs font-medium text-amber-700">
                {pendingCount} finding(s) pending review
              </span>
            )}
          </div>
        </section>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* LEFT: fields + images */}
        <div className="space-y-4">
          <section className="rounded-xl border border-neutral-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-neutral-900">
              Extracted fields
            </h2>
            <ul className="space-y-2">
              {insp.fields.map((f) => (
                <li key={f.id} className="text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                      {f.field}
                    </span>
                    <button
                      onClick={() => {
                        setEditingField(f);
                        setFieldDraft(f.raw ?? "");
                      }}
                      className="text-xs text-neutral-900 underline underline-offset-2 hover:text-neutral-600"
                    >
                      Edit
                    </button>
                  </div>
                  <div className="mt-0.5 flex items-baseline gap-2">
                    <span className="font-medium text-neutral-900">
                      {f.raw ?? "—"}
                    </span>
                    {f.confidence != null && (
                      <span
                        className={cx(
                          "text-[11px] tabular-nums",
                          f.confidence >= 0.8
                            ? "text-emerald-600"
                            : f.confidence >= 0.6
                              ? "text-amber-600"
                              : "text-red-600"
                        )}
                      >
                        {Math.round(f.confidence * 100)}%
                      </span>
                    )}
                    {f.is_edited && (
                      <span className="text-[10px] font-medium text-violet-600">
                        EDITED
                      </span>
                    )}
                  </div>
                </li>
              ))}
            </ul>

            {editingField && (
              <div className="mt-3 rounded-md border border-neutral-200 bg-neutral-50 p-3">
                <label className="mb-1 block text-xs font-medium text-neutral-600">
                  Override raw value ({editingField.field})
                </label>
                <input
                  value={fieldDraft}
                  onChange={(e) => setFieldDraft(e.target.value)}
                  className="w-full rounded-md border border-neutral-300 bg-white px-2 py-1.5 text-sm outline-none"
                />
                <div className="mt-2 flex gap-2">
                  <button
                    onClick={saveFieldEdit}
                    disabled={busy}
                    className="rounded bg-neutral-900 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                  >
                    Save & re-assess
                  </button>
                  <button
                    onClick={() => setEditingField(null)}
                    className="rounded border border-neutral-300 px-3 py-1.5 text-xs text-neutral-600"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-neutral-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-neutral-900">
              Source images ({insp.images.length})
            </h2>
            <ul className="space-y-1">
              {insp.images.map((img) => (
                <li
                  key={img.id}
                  onClick={() => {
                    setSelectedImageId(img.id);
                    setSelectedFinding(null);
                  }}
                  className={cx(
                    "cursor-pointer rounded-md border px-3 py-2 text-sm",
                    selectedImageId === img.id
                      ? "border-neutral-900 bg-neutral-100"
                      : "border-neutral-200 hover:bg-neutral-50"
                  )}
                >
                  <div className="flex justify-between">
                    <span className="font-medium text-neutral-900">
                      {img.type}
                    </span>
                    <span className="text-xs text-neutral-500">
                      {img.width}×{img.height}
                    </span>
                  </div>
                  <div className="mt-0.5 truncate text-[11px] text-neutral-500">
                    sha256 {img.sha256.slice(0, 12)}…
                  </div>
                  {img.quality_score_json?.score != null && (
                    <div className="mt-0.5 text-[11px] text-amber-600">
                      Quality {Math.round(img.quality_score_json.score * 100)}%
                      {img.quality_score_json.warnings?.length
                        ? ` · ${img.quality_score_json.warnings.join(", ")}`
                        : ""}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </section>
        </div>

        {/* CENTER: assessments + findings */}
        <section className="rounded-xl border border-neutral-200 bg-white p-4 lg:col-span-1">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Assessments ({insp.assessments.length})
          </h2>
          <div className="space-y-4">
            {insp.assessments.map((a) => (
              <div
                key={a.id}
                className="rounded-lg border border-neutral-200 bg-neutral-50 p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-semibold text-neutral-900">
                    {a.rule_id}
                  </span>
                  <ResultBadge result={a.result} />
                </div>
                {a.detail && (
                  <p className="mt-1.5 text-xs leading-relaxed text-neutral-600">
                    {a.detail}
                  </p>
                )}
                {a.findings.length > 0 && (
                  <ul className="mt-2 space-y-2 border-t border-neutral-200 pt-2">
                    {a.findings.map((f) => (
                      <li
                        key={f.id}
                        onClick={() => {
                          setSelectedFinding(f);
                          setSelectedImageId(f.image_id ?? selectedImageId);
                        }}
                        className={cx(
                          "cursor-pointer rounded-md border p-2 text-xs transition-colors",
                          selectedFinding?.id === f.id
                            ? "border-neutral-900 bg-white"
                            : "border-neutral-200 bg-white hover:border-neutral-400"
                        )}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className={cx(
                              "font-semibold",
                              severityColor(f.severity)
                            )}
                          >
                            {f.severity.toUpperCase()}
                          </span>
                          <ReviewBadge status={f.review_status} />
                        </div>
                        <p className="mt-1 text-neutral-700">{f.summary}</p>
                        {f.confidence != null && (
                          <div className="mt-0.5 text-[10px] tabular-nums text-neutral-500">
                            confidence {Math.round(f.confidence * 100)}% ·{" "}
                            {f.ruleset_version}
                          </div>
                        )}
                        <div className="mt-2 flex flex-wrap gap-1">
                          {f.review_status === "pending" && (
                            <>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  patchFinding(f, "CONFIRMED");
                                }}
                                disabled={busy}
                                className="rounded bg-emerald-600 px-2 py-1 text-[10px] font-semibold text-white disabled:opacity-50"
                              >
                                Confirm
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  patchFinding(f, "REJECTED");
                                }}
                                disabled={busy}
                                className="rounded bg-neutral-800 px-2 py-1 text-[10px] font-semibold text-white disabled:opacity-50"
                              >
                                Reject
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  patchFinding(f, "MANUAL VERIFICATION");
                                }}
                                disabled={busy}
                                className="rounded bg-amber-500 px-2 py-1 text-[10px] font-semibold text-white disabled:opacity-50"
                              >
                                Manual
                              </button>
                            </>
                          )}
                          {selectedFinding?.id === f.id && (
                            <input
                              value={comment}
                              onChange={(e) => setComment(e.target.value)}
                              placeholder="Review comment (stored in audit trail)"
                              className="w-full rounded border border-neutral-300 px-2 py-1 text-[10px] outline-none"
                            />
                          )}
                        </div>
                        {f.review_comment && (
                          <p className="mt-1.5 border-t border-neutral-100 pt-1 text-[10px] text-neutral-500">
                            “{f.review_comment}”
                            {f.reviewed_at && ` · ${formatDateTime(f.reviewed_at)}`}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* RIGHT: evidence */}
        <section className="rounded-xl border border-neutral-200 bg-white p-4">
          <h2 className="mb-3 text-sm font-semibold text-neutral-900">
            Evidence
          </h2>
          {selectedImage ? (
            <div>
              <div className="flex items-center justify-between text-xs text-neutral-500">
                <span>{selectedImage.type}</span>
                <span>
                  {selectedFinding
                    ? selectedFinding.rule_id
                    : "Image (no finding selected)"}
                </span>
              </div>
              <div className="relative mt-2 overflow-hidden rounded-lg border border-neutral-200 bg-neutral-50">
                {imageUrls[selectedImage.id] ? (
                  <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={imageUrls[selectedImage.id]}
                      alt={selectedImage.type}
                      className="w-full"
                    />
                    {selectedBbox && selectedImage.width && selectedImage.height && (
                      <div
                        className="pointer-events-none absolute border-2 border-red-500 bg-red-500/10"
                        style={{
                          left: `${(selectedBbox.x1 / selectedImage.width) * 100}%`,
                          top: `${(selectedBbox.y1 / selectedImage.height) * 100}%`,
                          width: `${((selectedBbox.x2 - selectedBbox.x1) / selectedImage.width) * 100}%`,
                          height: `${((selectedBbox.y2 - selectedBbox.y1) / selectedImage.height) * 100}%`,
                        }}
                      />
                    )}
                  </>
                ) : (
                  <div className="flex h-48 items-center justify-center text-xs text-neutral-400">
                    Loading image…
                  </div>
                )}
              </div>
              {selectedFinding && (
                <div className="mt-3 rounded-md border border-neutral-200 bg-neutral-50 p-3 text-xs">
                  <div className="mb-1 flex items-center justify-between">
                    <span className="font-mono font-semibold text-neutral-900">
                      {selectedFinding.rule_id}
                    </span>
                    <ResultBadge result={selectedFinding.automated_result} />
                  </div>
                  <p className="text-neutral-700">{selectedFinding.summary}</p>
                  <p className="mt-2 text-[10px] text-neutral-500">
                    image #{selectedFinding.image_id} · ocr block #
                    {selectedFinding.ocr_block_id ?? "—"} ·{" "}
                    {selectedFinding.ruleset_version}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-neutral-500">No images on this inspection.</p>
          )}
        </section>
      </div>
    </AuthShell>
  );
}