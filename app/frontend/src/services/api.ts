import axios from "axios";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
    // Demo auth token — replace with real JWT in production
    Authorization: "Bearer insureco-demo-token",
  },
  timeout: 15000,
});

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Policyholder {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  date_of_birth?: string;
  address?: string;
}

export interface Policy {
  id: string;
  policyholder_id: string;
  policy_type: "AUTO" | "HOME" | "LIFE" | "COMMERCIAL";
  policy_number: string;
  premium_amount: number | string;
  coverage_amount: number | string;
  start_date: string;
  end_date: string;
  status: "ACTIVE" | "EXPIRED" | "CANCELLED" | "PENDING";
}

export interface Claim {
  id: string;
  policy_id: string;
  claim_number: string;
  claim_type: string;
  description: string;
  amount_requested: number | string;
  amount_approved?: number | string | null;
  status: "SUBMITTED" | "UNDER_REVIEW" | "APPROVED" | "REJECTED" | "PAID";
  incident_date: string;
  filed_at?: string;
  updated_at?: string;
}

export interface Document {
  id: string;
  document_type: string;
  file_name: string;
  claim_id?: string;
  policy_id?: string;
}

export interface PresignResponse {
  upload_url: string;
  file_key: string;
}

export interface QuoteResult {
  premium_monthly: number;
  premium_annual: number;
  coverage_details: Record<string, string | number>;
}

// ── API functions ─────────────────────────────────────────────────────────────

export const api = {
  // Health
  health: () =>
    client.get("/health").then((r) => r.data),

  // Policyholders
  createPolicyholder: (data: Partial<Policyholder>) =>
    client.post<Policyholder>("/api/policyholders", data).then((r) => r.data),

  getPolicyholder: (id: string) =>
    client.get<Policyholder>(`/api/policyholders/${id}`).then((r) => r.data),

  listPolicyholders: (params?: { skip?: number; limit?: number }) =>
    client
      .get<Policyholder[]>("/api/policyholders", { params })
      .then((r) => r.data),

  updatePolicyholder: (id: string, data: Partial<Policyholder>) =>
    client
      .put<Policyholder>(`/api/policyholders/${id}`, data)
      .then((r) => r.data),

  // Policies
  getPolicies: (params?: {
    status?: string;
    policy_type?: string;
    policyholder_id?: string;
    skip?: number;
    limit?: number;
  }) =>
    client.get<Policy[]>("/api/policies", { params }).then((r) => r.data),

  getPolicy: (id: string) =>
    client.get<Policy>(`/api/policies/${id}`).then((r) => r.data),

  createPolicy: (data: Partial<Policy>) =>
    client.post<Policy>("/api/policies", data).then((r) => r.data),

  updatePolicy: (id: string, data: Partial<Policy>) =>
    client.put<Policy>(`/api/policies/${id}`, data).then((r) => r.data),

  getPolicyDocuments: (id: string) =>
    client
      .get<Document[]>(`/api/policies/${id}/documents`)
      .then((r) => r.data),

  // Claims
  getClaims: (params?: {
    status?: string;
    policy_id?: string;
    skip?: number;
    limit?: number;
  }) =>
    client.get<Claim[]>("/api/claims", { params }).then((r) => r.data),

  getClaim: (id: string) =>
    client.get<Claim>(`/api/claims/${id}`).then((r) => r.data),

  createClaim: (data: {
    policy_id: string;
    incident_date: string;
    claim_type: string;
    description: string;
    amount_requested: number;
  }) =>
    client.post<Claim>("/api/claims", data).then((r) => r.data),

  updateClaim: (id: string, data: Partial<Claim>) =>
    client.put<Claim>(`/api/claims/${id}`, data).then((r) => r.data),

  approveClaim: (id: string, amount_approved: number, notes?: string) =>
    client
      .post<Claim>(`/api/claims/${id}/approve`, { amount_approved, notes })
      .then((r) => r.data),

  rejectClaim: (id: string, reason: string) =>
    client
      .post<Claim>(`/api/claims/${id}/reject`, { reason })
      .then((r) => r.data),

  // Documents
  presignDocument: (data: {
    file_name: string;
    document_type: string;
    content_type: string;
    claim_id?: string;
    policy_id?: string;
  }) =>
    client
      .post<PresignResponse>("/api/documents/presign", data)
      .then((r) => r.data),

  registerDocument: (data: {
    file_key: string;
    file_name: string;
    document_type: string;
    claim_id?: string;
    policy_id?: string;
  }) =>
    client.post<Document>("/api/documents", data).then((r) => r.data),

  getDocumentDownloadUrl: (id: string) =>
    client
      .get<{ download_url: string; file_name: string }>(
        `/api/documents/${id}`
      )
      .then((r) => r.data),

  // Quotes
  quoteAuto: (data: {
    driver_age: number;
    vehicle_year: number;
    coverage_type: string;
    annual_mileage: number;
  }) =>
    client.post<QuoteResult>("/api/quotes/auto", data).then((r) => r.data),

  quoteHome: (data: {
    home_value: number;
    location_risk: string;
    home_age_years: number;
    coverage_type: string;
  }) =>
    client.post<QuoteResult>("/api/quotes/home", data).then((r) => r.data),

  quoteLife: (data: {
    age: number;
    health_score: number;
    coverage_amount: number;
    term_years: number;
  }) =>
    client.post<QuoteResult>("/api/quotes/life", data).then((r) => r.data),
};
