"use client";

import { useEffect, useRef, useState } from "react";
import { use } from "react";
import { useRouter } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { api } from "@/lib/api";
import { InspectionDetail } from "@/lib/types";

const STAGES = [
  { key: "queued", label: "Queued" },
  { key: "quality", label: "Quality check" },
  { key: "ocr", label: "OCR (detect + recognize)" },
  { key: "extraction", label: "Field extraction" },
  { key: "rules", label: "Rule assessment" },
  { key: "evidence", label: "Evidence linkage" },
] as const;

const TERMINAL = new Set(["ready_for_review", "reviewed", "closed", "FAILED"]);

export default function ProcessingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [insp, setInsp] = useState<InspectionDetail | null>(null);
  const [stage, setStage] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const tick = () => setElapsed((e) => e + 1);
    timer.current = setInterval(tick, 1000);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let poll: ReturnType<typeof setInterval> | null = null;

    async function refresh() {
      try {
        const data = await api.getInspection(Number(id));
        if (cancelled) return;
        setInsp(data);
        if (data.status === "processing") {
          const imag = data.images.filter((i) => i.processed_url).length;
          const fieldCount = data.fields.length;
          if (fieldCount >= 2) setStage(3);
          else if (imag > 0) setStage(2);
          else setStage(1);
        } else if (TERMINAL.has(data.status)) {
          if (poll) clearInterval(poll);
          if (timer.current) clearInterval(timer.current);
          if (data.status === "FAILED") {
            setStage(5);
          } else {
            setStage(5);
            setTimeout(() => router.replace(`/inspections/${data.id}/assessment`), 900);
          }
        }
      } catch {
        // transient; keep polling
      }
    }

    refresh();
    poll = setInterval(refresh, 2500);
    return () => {
      cancelled = true;
      if (poll) clearInterval(poll);
    };
  }, [id, router]);

  const failed = insp?.status === "FAILED";
  const mins = Math.floor(elapsed / 60);
  const secs = String(elapsed % 60).padStart(2, "0");

  return (
    <AuthShell>
      <div className="mx-auto max-w-2xl">
        <h1 className="text-xl font-bold text-neutral-900">
          Processing {insp?.public_id ?? ""}
        </h1>
        <p className="mb-8 text-sm text-neutral-500">
          Automated pipeline: quality → OCR → extraction → rules → evidence.
        </p>

        {failed ? (
          <div className="rounded-xl border border-red-300 bg-red-50 p-5 text-sm text-red-800">
            <div className="font-semibold">Processing failed</div>
            <div className="mt-1 text-xs">
              {insp?.process_error ?? "Unknown pipeline error"}
            </div>
          </div>
        ) : (
          <div className="rounded-xl border border-neutral-200 bg-white p-6">
            <div className="mb-6 flex items-center gap-3 text-sm text-neutral-600">
              <span className="inline-block h-3 w-3 animate-pulse rounded-full bg-emerald-500" />
              Analyzing product labels
              <span className="ml-auto tabular-nums text-neutral-400">
                {mins}:{secs}
              </span>
            </div>
            <ol>
              {STAGES.map((s, i) => {
                const done = i <= stage;
                const active = i === stage;
                return (
                  <li key={s.key} className="relative flex gap-3 pb-5 last:pb-0">
                    {i < STAGES.length - 1 && (
                      <span
                        className={`absolute left-2 top-5 h-full w-px ${
                          i < stage ? "bg-neutral-900" : "bg-neutral-200"
                        }`}
                      />
                    )}
                    <span
                      className={`relative z-10 mt-0.5 flex h-4 w-4 items-center justify-center rounded-full text-[9px] ${
                        done
                          ? "bg-neutral-900 text-white"
                          : "border border-neutral-300 bg-white text-neutral-400"
                      }`}
                    >
                      {done ? "✓" : ""}
                    </span>
                    <span
                      className={`text-sm ${
                        active ? "font-semibold text-neutral-900" : "text-neutral-600"
                      } ${done && !active ? "text-neutral-900" : ""}`}
                    >
                      {s.label}
                      {active && !done && (
                        <span className="ml-2 text-xs text-neutral-400">
                          (in progress…)
                        </span>
                      )}
                    </span>
                  </li>
                );
              })}
            </ol>
          </div>
        )}
      </div>
    </AuthShell>
  );
}