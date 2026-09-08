"use client";

import Link from "next/link";
import { AuthShell } from "@/components/AuthShell";

export default function ProductsPage() {
  return (
    <AuthShell>
      <h1 className="mb-2 text-xl font-bold text-neutral-900">Products</h1>
      <p className="mb-4 max-w-xl text-sm text-neutral-500">
        The product catalogue is a post-MVP feature (PRD §40). Product-level
        data is currently derived from inspection extractions.
      </p>
      <div className="max-w-xl rounded-xl border border-neutral-200 bg-white p-5 text-sm">
        <div className="mb-2 font-semibold text-neutral-900">What you can do now</div>
        <ul className="list-inside list-disc space-y-1 text-neutral-700">
          <li>Open an inspection to see extracted product fields.</li>
          <li>Check rule assessments linked to that product.</li>
          <li>
            Use{" "}
            <Link
              href="/inspections"
              className="font-medium text-neutral-900 underline underline-offset-2"
            >
              search
            </Link>{" "}
            to find inspections by product name / origin.
          </li>
        </ul>
      </div>
    </AuthShell>
  );
}