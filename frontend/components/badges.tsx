import { InspectionStatus } from "@/lib/types";
import { cx } from "@/lib/format";

const STATUS_STYLES: Record<InspectionStatus, string> = {
  draft: "bg-neutral-100 text-neutral-700 border-neutral-300",
  processing: "bg-amber-50 text-amber-700 border-amber-300",
  ready_for_review: "bg-sky-50 text-sky-700 border-sky-300",
  reviewed: "bg-violet-50 text-violet-700 border-violet-300",
  closed: "bg-emerald-50 text-emerald-700 border-emerald-300",
  FAILED: "bg-red-50 text-red-700 border-red-300",
};

const STATUS_LABEL: Record<InspectionStatus, string> = {
  draft: "Draft",
  processing: "Processing",
  ready_for_review: "Ready for review",
  reviewed: "Reviewed",
  closed: "Closed",
  FAILED: "Failed",
};

export function StatusBadge({ status }: { status: InspectionStatus }) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium",
        STATUS_STYLES[status] ?? STATUS_STYLES.draft
      )}
    >
      {STATUS_LABEL[status] ?? status}
    </span>
  );
}

const RESULT_STYLES: Record<string, string> = {
  PASS: "border-emerald-300 bg-emerald-50 text-emerald-700",
  "POTENTIAL NON-COMPLIANCE":
    "border-red-300 bg-red-50 text-red-700",
  "NEEDS VERIFICATION":
    "border-amber-300 bg-amber-50 text-amber-700",
  "NOT APPLICABLE": "border-neutral-300 bg-neutral-100 text-neutral-600",
};

export function ResultBadge({ result }: { result: string }) {
  return (
    <span
      className={cx(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold",
        RESULT_STYLES[result] ?? RESULT_STYLES["NOT APPLICABLE"]
      )}
    >
      {result}
    </span>
  );
}

export function ReviewBadge({ status }: { status: string }) {
  switch (status) {
    case "CONFIRMED":
      return (
        <span className="inline-flex items-center rounded-md bg-emerald-600 px-2 py-0.5 text-[11px] font-semibold text-white">
          CONFIRMED
        </span>
      );
    case "REJECTED":
      return (
        <span className="inline-flex items-center rounded-md bg-neutral-800 px-2 py-0.5 text-[11px] font-semibold text-white">
          REJECTED
        </span>
      );
    case "MANUAL VERIFICATION":
      return (
        <span className="inline-flex items-center rounded-md bg-amber-500 px-2 py-0.5 text-[11px] font-semibold text-white">
          MANUAL VERIFICATION
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center rounded-md border border-neutral-300 bg-white px-2 py-0.5 text-[11px] font-medium text-neutral-600">
          Pending review
        </span>
      );
  }
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-red-600";
    case "high":
      return "text-orange-600";
    case "medium":
      return "text-amber-600";
    default:
      return "text-neutral-600";
  }
}