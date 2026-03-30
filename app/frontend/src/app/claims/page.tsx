"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Claim } from "@/services/api";
import ClaimStatusBadge from "@/components/ClaimStatusBadge";

type FilterStatus =
  | ""
  | "SUBMITTED"
  | "UNDER_REVIEW"
  | "APPROVED"
  | "REJECTED"
  | "PAID";

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("");

  useEffect(() => {
    async function fetchClaims() {
      setLoading(true);
      try {
        const data = await api.getClaims({
          status: filterStatus || undefined,
          limit: 100,
        });
        setClaims(data);
      } catch (err) {
        setError("Failed to load claims.");
      } finally {
        setLoading(false);
      }
    }
    fetchClaims();
  }, [filterStatus]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Claims</h1>
          <p className="text-gray-500 mt-1 text-sm">
            View and manage all insurance claims.
          </p>
        </div>
        <Link href="/claims/new" className="btn-primary text-sm">
          + File New Claim
        </Link>
      </div>

      {/* Status filter tabs */}
      <div className="flex flex-wrap gap-2">
        {(
          [
            { value: "", label: "All" },
            { value: "SUBMITTED", label: "Submitted" },
            { value: "UNDER_REVIEW", label: "Under Review" },
            { value: "APPROVED", label: "Approved" },
            { value: "REJECTED", label: "Rejected" },
            { value: "PAID", label: "Paid" },
          ] as { value: FilterStatus; label: string }[]
        ).map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setFilterStatus(value)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filterStatus === value
                ? "bg-brand-navy text-white"
                : "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-md px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : claims.length === 0 ? (
        <div className="card py-16 text-center">
          <p className="text-gray-400 text-sm">No claims found.</p>
          <Link href="/claims/new" className="mt-4 btn-primary inline-block text-sm">
            File your first claim
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">{claims.length} claim(s) found</p>
          {claims.map((claim) => (
            <div
              key={claim.id}
              className="card px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:shadow-md transition-shadow"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-semibold text-gray-800">
                    {claim.claim_number}
                  </span>
                  <ClaimStatusBadge status={claim.status} />
                </div>
                <p className="text-sm text-gray-500">
                  <span className="font-medium text-gray-700">{claim.claim_type}</span>
                  {" — "}
                  {claim.description.length > 80
                    ? claim.description.slice(0, 80) + "..."
                    : claim.description}
                </p>
              </div>
              <div className="flex items-center gap-6 text-sm shrink-0">
                <div className="text-right">
                  <p className="text-xs text-gray-400">Requested</p>
                  <p className="font-semibold text-gray-800">
                    {formatCurrency(parseFloat(String(claim.amount_requested)))}
                  </p>
                </div>
                {claim.amount_approved != null && (
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Approved</p>
                    <p className="font-semibold text-green-700">
                      {formatCurrency(parseFloat(String(claim.amount_approved)))}
                    </p>
                  </div>
                )}
                <div className="text-right">
                  <p className="text-xs text-gray-400">Filed</p>
                  <p className="text-gray-600">
                    {claim.filed_at ? formatDate(claim.filed_at) : "—"}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
