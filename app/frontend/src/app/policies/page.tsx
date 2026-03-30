"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, Policy } from "@/services/api";
import PolicyCard from "@/components/PolicyCard";

type FilterStatus = "" | "ACTIVE" | "EXPIRED" | "CANCELLED" | "PENDING";
type FilterType = "" | "AUTO" | "HOME" | "LIFE" | "COMMERCIAL";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<FilterStatus>("");
  const [filterType, setFilterType] = useState<FilterType>("");

  useEffect(() => {
    async function fetchPolicies() {
      try {
        const data = await api.getPolicies({
          status: filterStatus || undefined,
          policy_type: filterType || undefined,
          limit: 100,
        });
        setPolicies(data);
      } catch (err) {
        setError("Failed to load policies.");
      } finally {
        setLoading(false);
      }
    }
    fetchPolicies();
  }, [filterStatus, filterType]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Policies</h1>
          <p className="text-gray-500 mt-1 text-sm">
            Manage all auto, home, life, and commercial insurance policies.
          </p>
        </div>
        <button className="btn-primary flex items-center gap-2 text-sm">
          + New Policy
        </button>
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4 items-center">
        <div>
          <label className="label">Policy Type</label>
          <select
            className="input-field w-44"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as FilterType)}
          >
            <option value="">All Types</option>
            <option value="AUTO">Auto</option>
            <option value="HOME">Home</option>
            <option value="LIFE">Life</option>
            <option value="COMMERCIAL">Commercial</option>
          </select>
        </div>
        <div>
          <label className="label">Status</label>
          <select
            className="input-field w-44"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="PENDING">Pending</option>
            <option value="EXPIRED">Expired</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
        {(filterStatus || filterType) && (
          <button
            className="btn-secondary text-sm mt-5"
            onClick={() => {
              setFilterStatus("");
              setFilterType("");
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Content */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-md px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-44 bg-gray-200 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : policies.length === 0 ? (
        <div className="card py-16 text-center">
          <p className="text-gray-400 text-sm">
            No policies found matching the selected filters.
          </p>
        </div>
      ) : (
        <>
          <p className="text-sm text-gray-500">{policies.length} policy(ies) found</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {policies.map((policy) => (
              <PolicyCard key={policy.id} policy={policy} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
