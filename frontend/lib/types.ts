export type Role = "inspector" | "reviewer" | "admin" | "auditor";

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type InspectionStatus =
  | "draft"
  | "processing"
  | "ready_for_review"
  | "reviewed"
  | "closed"
  | "FAILED";

export interface InspectionListItem {
  id: number;
  public_id: string;
  location: string;
  channel: string;
  inspection_date: string;
  category: string | null;
  status: InspectionStatus;
  ruleset_version: string | null;
  created_at: string;
  image_count: number;
  finding_count: number;
}

export interface InspectionListResponse {
  items: InspectionListItem[];
  total: number;
}

export interface InspectionImage {
  id: number;
  type: string;
  original_url: string;
  processed_url: string | null;
  sha256: string;
  width: number | null;
  height: number | null;
  quality_score_json: { score?: number; warnings?: string[]; recommendation?: string } | null;
}

export interface ExtractedField {
  id: number;
  field: string;
  raw: string | null;
  normalized: Record<string, unknown> | null;
  confidence: number | null;
  source_ocr_ids: number[] | null;
  is_edited: boolean;
}

export type AutomatedResult =
  | "PASS"
  | "POTENTIAL NON-COMPLIANCE"
  | "NEEDS VERIFICATION"
  | "NOT APPLICABLE";

export type ReviewStatus = "pending" | "CONFIRMED" | "REJECTED" | "MANUAL VERIFICATION";

export interface Finding {
  id: number;
  rule_id: string;
  ruleset_version: string;
  image_id: number | null;
  ocr_block_id: number | null;
  bbox: { x1: number; y1: number; x2: number; y2: number } | null;
  summary: string;
  severity: string;
  confidence: number | null;
  automated_result: AutomatedResult;
  review_status: ReviewStatus;
  review_comment: string | null;
  reviewed_at: string | null;
}

export interface Assessment {
  id: number;
  rule_id: string;
  ruleset_version: string;
  result: AutomatedResult;
  evidence_json: Record<string, unknown> | null;
  detail: string | null;
  findings: Finding[];
}

export interface InspectionDetail extends InspectionListItem {
  inspector_id: number;
  package_structure: string;
  origin: string;
  special_status: string | null;
  product_name_hint: string | null;
  process_error: string | null;
  closed_at: string | null;
  images: InspectionImage[];
  fields: ExtractedField[];
  assessments: Assessment[];
}

export interface DashboardData {
  total_inspections: number;
  status_breakdown: Record<string, number>;
  channel_breakdown: Record<string, number>;
  top_categories: { category: string; count: number }[];
  total_images: number;
  assessment_breakdown: Record<string, number>;
  findings: {
    total: number;
    reviewed: number;
    pending_review: number;
    flagged_potential: number;
    review_breakdown: Record<string, number>;
  };
  created_this_month: number;
}

export interface CreateInspectionInput {
  location: string;
  channel: string;
  inspection_date: string;
  category?: string;
  package_structure: string;
  origin: string;
  special_status?: string;
  product_name_hint?: string;
}

export interface UploadResponse {
  created: InspectionImage[];
  warnings: string[];
}

export interface Rule {
  id: number;
  rule_id: string;
  title: string;
  version: string;
  status: "draft" | "published" | "withdrawn";
  effective_from: string | null;
  severity: string;
}

export interface RuleListResponse {
  version: string;
  rules: Rule[];
}

export interface CategorySuggestion {
  current: string | null;
  suggestions: { category: string; confidence: number; basis: string }[];
}