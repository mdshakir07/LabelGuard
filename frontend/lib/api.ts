"use client";

import {
  CategorySuggestion,
  CreateInspectionInput,
  DashboardData,
  InspectionDetail,
  InspectionListResponse,
  LoginResponse,
  RuleListResponse,
  UploadResponse,
  User,
} from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const TOKEN_KEY = "mm_token";
const USER_KEY = "mm_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
  document.cookie = `mm_token=${token}; path=/; max-age=28800; samesite=lax`;
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setUser(user: User): void {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  document.cookie = "mm_token=; path=/; max-age=0";
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (res.status === 401 && typeof window !== "undefined") {
    clearAuth();
    // eslint-disable-next-line @next/next/no-location-assign-relative-destination
    window.location.href = "/login";
    throw new ApiError("Session expired", 401);
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // ignore body parse errors
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return undefined as T;
  const ct = res.headers.get("content-type") ?? "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  return (await res.blob()) as unknown as T;
}

export const api = {
  login(email: string, password: string) {
    return request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  getDashboard() {
    return request<DashboardData>("/dashboard");
  },

  listRules() {
    return request<RuleListResponse>("/rules");
  },

  listInspections(params: Record<string, string> = {}) {
    const qs = new URLSearchParams(params).toString();
    return request<InspectionListResponse>(`/inspections${qs ? `?${qs}` : ""}`);
  },

  getInspection(id: number) {
    return request<InspectionDetail>(`/inspections/${id}`);
  },

  createInspection(body: CreateInspectionInput) {
    return request<InspectionDetail>("/inspections", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  async uploadImages(id: number, files: File[], typ: string) {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("typ", typ);
    return request<UploadResponse>(`/inspections/${id}/images`, {
      method: "POST",
      body: form,
    });
  },

  startProcessing(id: number) {
    return request<{ status: string; inspection_id: number; public_id: string }>(
      `/inspections/${id}/process`,
      { method: "POST", body: "{}" }
    );
  },

  reAssess(id: number) {
    return request(`/inspections/${id}/assess`, { method: "POST", body: "{}" });
  },

  getCategorySuggestion(id: number) {
    return request<CategorySuggestion>(`/inspections/${id}/category-suggestion`);
  },

  setCategory(id: number, category: string) {
    return request<InspectionDetail>(`/inspections/${id}/category`, {
      method: "PATCH",
      body: JSON.stringify({ category }),
    });
  },

  reviewInspection(id: number) {
    return request<InspectionDetail>(`/inspections/${id}/review`, {
      method: "POST",
      body: "{}",
    });
  },

  closeInspection(id: number) {
    return request<InspectionDetail>(`/inspections/${id}/close`, {
      method: "POST",
      body: "{}",
    });
  },

  reviewFinding(id: number, reviewStatus: string, comment: string) {
    return request(`/findings/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ review_status: reviewStatus, review_comment: comment }),
    });
  },

  editField(inspectionId: number, fieldId: number, raw: string) {
    return request(`/inspections/${inspectionId}/fields/${fieldId}`, {
      method: "PATCH",
      body: JSON.stringify({ raw }),
    });
  },

  generateReport(id: number, format: "pdf" | "docx") {
    return request<{ status: string; format: string }>(`/inspections/${id}/report`, {
      method: "POST",
      body: JSON.stringify({ format }),
    });
  },

  async fetchImageUrl(inspectionId: number, imageId: number): Promise<string> {
    const blob = await request<Blob>(`/inspections/${inspectionId}/images/${imageId}/file`);
    return URL.createObjectURL(blob);
  },

  async downloadReport(id: number, format: "pdf" | "docx"): Promise<void> {
    const token = getToken();
    const res = await fetch(`${API_BASE}/inspections/${id}/report?fmt=${format}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError(`HTTP ${res.status}`, res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },
};