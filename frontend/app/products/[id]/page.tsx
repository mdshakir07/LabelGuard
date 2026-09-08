"use client";

import Link from "next/link";
import { use } from "react";
import { AuthShell } from "@/components/AuthShell";

export default function ProductDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  return (
    <AuthShell>
      <div className="mb-5">
        <Link href="/products" className="text-sm text-neutral-600 hover:underline">
          ← Products
        </Link>
        <h1 className="mt-1 text-xl font-bold text-neutral-900">
          Product #{id}
        </h1>
      </div>
      <div className="max-w-xl rounded-xl border border-neutral-200 bg-white p-5 text-sm text-neutral-600">
        Product profiles are a deferred feature (PRD §40, P1). Inspection-level
        data is available from the inspection record.
      </div>
    </AuthShell>
  );
}