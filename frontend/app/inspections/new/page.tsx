"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthShell } from "@/components/AuthShell";
import { api, ApiError } from "@/lib/api";

const CHANNELS = ["retail", "ecommerce", "institutional", "industrial"];
const STRUCTURES = ["single", "multi_product", "multi_unit", "promotional"];
const ORIGINS = ["domestic", "imported"];

export default function NewInspectionPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    location: "",
    channel: "retail",
    inspection_date: new Date().toISOString().slice(0, 10),
    category: "",
    package_structure: "single",
    origin: "domestic",
    special_status: "",
    product_name_hint: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function set<K extends keyof typeof form>(key: K, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const insp = await api.createInspection({
        location: form.location.trim(),
        channel: form.channel,
        inspection_date: form.inspection_date,
        category: form.category.trim() || undefined,
        package_structure: form.package_structure,
        origin: form.origin,
        special_status: form.special_status.trim() || undefined,
        product_name_hint: form.product_name_hint.trim() || undefined,
      });
      router.push(`/inspections/${insp.id}/upload`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  const field =
    "w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-sm outline-none focus:border-neutral-500";
  const label = "mb-1 block text-xs font-medium text-neutral-600";

  return (
    <AuthShell>
      <div className="mb-5">
        <h1 className="text-xl font-bold text-neutral-900">New inspection</h1>
        <p className="text-sm text-neutral-500">
          Describe the place of inspection — images are captured on the next
          step.
        </p>
      </div>

      <form
        onSubmit={submit}
        className="max-w-xl rounded-xl border border-neutral-200 bg-white p-5"
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className={label}>Location</label>
            <input
              value={form.location}
              onChange={(e) => set("location", e.target.value)}
              placeholder="e.g. Kirana store, Sector 18, New Delhi"
              className={field}
            />
          </div>
          <div>
            <label className={label}>Sales channel</label>
            <select
              value={form.channel}
              onChange={(e) => set("channel", e.target.value)}
              className={field}
            >
              {CHANNELS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={label}>Inspection date</label>
            <input
              type="date"
              value={form.inspection_date}
              onChange={(e) => set("inspection_date", e.target.value)}
              className={field}
            />
          </div>
          <div>
            <label className={label}>Category (optional)</label>
            <input
              value={form.category}
              onChange={(e) => set("category", e.target.value)}
              placeholder="e.g. food, beverages, textiles"
              className={field}
            />
          </div>
          <div>
            <label className={label}>Package structure</label>
            <select
              value={form.package_structure}
              onChange={(e) => set("package_structure", e.target.value)}
              className={field}
            >
              {STRUCTURES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={label}>Origin</label>
            <select
              value={form.origin}
              onChange={(e) => set("origin", e.target.value)}
              className={field}
            >
              {ORIGINS.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={label}>Special status (optional)</label>
            <input
              value={form.special_status}
              onChange={(e) => set("special_status", e.target.value)}
              placeholder="e.g. promotional, FMCG, imported"
              className={field}
            />
          </div>
          <div>
            <label className={label}>Product name hint (optional)</label>
            <input
              value={form.product_name_hint}
              onChange={(e) => set("product_name_hint", e.target.value)}
              placeholder="helps extraction"
              className={field}
            />
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-5 flex items-center gap-3">
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-neutral-900 px-5 py-2 text-sm font-semibold text-white hover:bg-neutral-700 disabled:opacity-60"
          >
            {busy ? "Creating…" : "Create & upload images"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded-md border border-neutral-300 px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
          >
            Cancel
          </button>
        </div>
      </form>
    </AuthShell>
  );
}