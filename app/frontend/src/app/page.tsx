"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Policy, Claim } from "@/services/api";
import StatsCard from "@/components/StatsCard";
import ClaimStatusBadge from "@/components/ClaimStatusBadge";

interface DashboardStats {
  activePolicies: number;
  openClaims: number;
  pendingRenewals: number;
  totalCoverage: number;
}

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

export default function DashboardPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [policiesRes, claimsRes] = await Promise.all([
          api.getPolicies({ limit: 50 }),
          api.getClaims({ limit: 50 }),
        ]);
        setPolicies(policiesRes);
        setClaims(claimsRes);
      } catch (err) {
        setError("Failed to load dashboard data. Please check your connection.");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const stats: DashboardStats = {
    activePolicies: policies.filter((p) => p.status === "ACTIVE").length,
    openClaims: claims.filter((c) =>
      ["SUBMITTED", "UNDER_REVIEW"].includes(c.status)
    ).length,
    pendingRenewals: policies.filter((p) => {
      if (p.status !== "ACTIVE") return false;
      const end = new Date(p.end_date);
      const now = new Date();
      const diff = (end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
      return diff <= 30 && diff > 0;
    }).length,
    totalCoverage: policies
      .filter((p) => p.status === "ACTIVE")
      .reduce((sum, p) => sum + parseFloat(String(p.coverage_amount)), 0),
  };

  const recentClaims = claims.slice(0, 5);
  const recentPolicies = policies.slice(0, 5);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-28 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">
          Welcome to InsureCo Insurance Portal — your policy and claims overview.
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-md px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          label="Active Policies"
          value={stats.activePolicies}
          icon="shield"
          color="blue"
        />
        <StatsCard
          label="Open Claims"
          value={stats.openClaims}
          icon="file"
          color="orange"
        />
        <StatsCard
          label="Pending Renewals"
          value={stats.pendingRenewals}
          icon="clock"
          color="yellow"
        />
        <StatsCard
          label="Total Coverage"
          value={formatCurrency(stats.totalCoverage)}
          icon="dollar"
          color="green"
        />
      </div>

      {/* Recent claims */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Claims</h2>
          <Link href="/claims" className="text-sm text-brand-red hover:text-brand-red-dark font-medium">
            View all
          </Link>
        </div>
        {recentClaims.length === 0 ? (
          <p className="px-6 py-8 text-center text-gray-400 text-sm">No claims on record.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Claim #</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Type</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Amount</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Filed</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recentClaims.map((claim) => (
                  <tr key={claim.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3 font-mono text-xs text-gray-700">{claim.claim_number}</td>
                    <td className="px-6 py-3 text-gray-700">{claim.claim_type}</td>
                    <td className="px-6 py-3 text-gray-700">
                      {formatCurrency(parseFloat(String(claim.amount_requested)))}
                    </td>
                    <td className="px-6 py-3">
                      <ClaimStatusBadge status={claim.status} />
                    </td>
                    <td className="px-6 py-3 text-gray-500">
                      {claim.filed_at ? formatDate(claim.filed_at) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent policies */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Policies</h2>
          <Link href="/policies" className="text-sm text-brand-red hover:text-brand-red-dark font-medium">
            View all
          </Link>
        </div>
        {recentPolicies.length === 0 ? (
          <p className="px-6 py-8 text-center text-gray-400 text-sm">No policies on record.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Policy #</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Type</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Coverage</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Premium/mo</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Status</th>
                  <th className="px-6 py-3 text-left font-medium text-gray-500">Expires</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recentPolicies.map((policy) => (
                  <tr key={policy.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-3 font-mono text-xs text-gray-700">{policy.policy_number}</td>
                    <td className="px-6 py-3 text-gray-700">{policy.policy_type}</td>
                    <td className="px-6 py-3 text-gray-700">
                      {formatCurrency(parseFloat(String(policy.coverage_amount)))}
                    </td>
                    <td className="px-6 py-3 text-gray-700">
                      {formatCurrency(parseFloat(String(policy.premium_amount)) / 12)}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          policy.status === "ACTIVE"
                            ? "bg-green-100 text-green-700"
                            : policy.status === "EXPIRED"
                            ? "bg-gray-100 text-gray-600"
                            : policy.status === "CANCELLED"
                            ? "bg-red-100 text-red-700"
                            : "bg-yellow-100 text-yellow-700"
                        }`}
                      >
                        {policy.status}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-gray-500">{formatDate(policy.end_date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
