"use client";

import { useState } from "react";
import { api } from "@/services/api";

type TabType = "auto" | "home" | "life";

interface QuoteResult {
  premium_monthly: number;
  premium_annual: number;
  coverage_details: Record<string, string | number>;
}

function formatCurrency(val: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
  }).format(val);
}

function QuoteResultCard({ result }: { result: QuoteResult }) {
  return (
    <div className="mt-6 bg-brand-navy text-white rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Your Estimated Premium</h3>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-gray-400 text-sm">Monthly Premium</p>
          <p className="text-3xl font-bold text-white">
            {formatCurrency(result.premium_monthly)}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-sm">Annual Premium</p>
          <p className="text-3xl font-bold text-white">
            {formatCurrency(result.premium_annual)}
          </p>
        </div>
      </div>
      <div className="border-t border-white/20 pt-4">
        <p className="text-gray-400 text-xs mb-2">Quote details</p>
        <div className="grid grid-cols-2 gap-1 text-sm text-gray-300">
          {Object.entries(result.coverage_details).map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <span className="capitalize">{k.replace(/_/g, " ")}:</span>
              <span className="text-white font-medium">{String(v)}</span>
            </div>
          ))}
        </div>
      </div>
      <p className="text-xs text-gray-500 mt-4">
        * This is an indicative quote only. Final premium may vary based on underwriting review.
      </p>
    </div>
  );
}

// ── Auto quote form ────────────────────────────────────────────────────────────

function AutoQuoteTab() {
  const [form, setForm] = useState({
    driver_age: 35,
    vehicle_year: 2020,
    coverage_type: "COMPREHENSIVE",
    annual_mileage: 12000,
  });
  const [result, setResult] = useState<QuoteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.quoteAuto(form);
      setResult(data);
    } catch {
      setError("Failed to calculate quote. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Driver Age</label>
          <input
            type="number"
            className="input-field"
            min={16}
            max={100}
            value={form.driver_age}
            onChange={(e) =>
              setForm((f) => ({ ...f, driver_age: parseInt(e.target.value) }))
            }
          />
        </div>
        <div>
          <label className="label">Vehicle Year</label>
          <input
            type="number"
            className="input-field"
            min={1990}
            max={2025}
            value={form.vehicle_year}
            onChange={(e) =>
              setForm((f) => ({ ...f, vehicle_year: parseInt(e.target.value) }))
            }
          />
        </div>
        <div>
          <label className="label">Coverage Type</label>
          <select
            className="input-field"
            value={form.coverage_type}
            onChange={(e) =>
              setForm((f) => ({ ...f, coverage_type: e.target.value }))
            }
          >
            <option value="LIABILITY">Liability Only</option>
            <option value="COLLISION">Collision</option>
            <option value="COMPREHENSIVE">Comprehensive</option>
          </select>
        </div>
        <div>
          <label className="label">Annual Mileage</label>
          <input
            type="number"
            className="input-field"
            min={1000}
            max={100000}
            step={1000}
            value={form.annual_mileage}
            onChange={(e) =>
              setForm((f) => ({ ...f, annual_mileage: parseInt(e.target.value) }))
            }
          />
        </div>
      </div>
      {error && (
        <p className="text-red-600 text-sm">{error}</p>
      )}
      <button type="submit" disabled={loading} className="btn-primary w-full">
        {loading ? "Calculating..." : "Get Auto Quote"}
      </button>
      {result && <QuoteResultCard result={result} />}
    </form>
  );
}

// ── Home quote form ────────────────────────────────────────────────────────────

function HomeQuoteTab() {
  const [form, setForm] = useState({
    home_value: 350000,
    location_risk: "MEDIUM",
    home_age_years: 15,
    coverage_type: "STANDARD",
  });
  const [result, setResult] = useState<QuoteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.quoteHome(form);
      setResult(data);
    } catch {
      setError("Failed to calculate quote. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Home Value (USD)</label>
          <input
            type="number"
            className="input-field"
            min={50000}
            max={5000000}
            step={10000}
            value={form.home_value}
            onChange={(e) =>
              setForm((f) => ({ ...f, home_value: parseFloat(e.target.value) }))
            }
          />
        </div>
        <div>
          <label className="label">Home Age (years)</label>
          <input
            type="number"
            className="input-field"
            min={0}
            max={150}
            value={form.home_age_years}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                home_age_years: parseInt(e.target.value),
              }))
            }
          />
        </div>
        <div>
          <label className="label">Location Risk</label>
          <select
            className="input-field"
            value={form.location_risk}
            onChange={(e) =>
              setForm((f) => ({ ...f, location_risk: e.target.value }))
            }
          >
            <option value="LOW">Low Risk Area</option>
            <option value="MEDIUM">Medium Risk Area</option>
            <option value="HIGH">High Risk Area</option>
          </select>
        </div>
        <div>
          <label className="label">Coverage Type</label>
          <select
            className="input-field"
            value={form.coverage_type}
            onChange={(e) =>
              setForm((f) => ({ ...f, coverage_type: e.target.value }))
            }
          >
            <option value="BASIC">Basic</option>
            <option value="STANDARD">Standard</option>
            <option value="PREMIUM">Premium</option>
          </select>
        </div>
      </div>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <button type="submit" disabled={loading} className="btn-primary w-full">
        {loading ? "Calculating..." : "Get Home Quote"}
      </button>
      {result && <QuoteResultCard result={result} />}
    </form>
  );
}

// ── Life quote form ────────────────────────────────────────────────────────────

function LifeQuoteTab() {
  const [form, setForm] = useState({
    age: 35,
    health_score: 80,
    coverage_amount: 500000,
    term_years: 20,
  });
  const [result, setResult] = useState<QuoteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.quoteLife(form);
      setResult(data);
    } catch {
      setError("Failed to calculate quote. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Age</label>
          <input
            type="number"
            className="input-field"
            min={18}
            max={80}
            value={form.age}
            onChange={(e) =>
              setForm((f) => ({ ...f, age: parseInt(e.target.value) }))
            }
          />
        </div>
        <div>
          <label className="label">
            Health Score (1-100)
            <span className="text-gray-400 font-normal ml-1">— 100 = Excellent</span>
          </label>
          <input
            type="number"
            className="input-field"
            min={1}
            max={100}
            value={form.health_score}
            onChange={(e) =>
              setForm((f) => ({ ...f, health_score: parseInt(e.target.value) }))
            }
          />
        </div>
        <div>
          <label className="label">Coverage Amount (USD)</label>
          <input
            type="number"
            className="input-field"
            min={50000}
            max={10000000}
            step={50000}
            value={form.coverage_amount}
            onChange={(e) =>
              setForm((f) => ({
                ...f,
                coverage_amount: parseFloat(e.target.value),
              }))
            }
          />
        </div>
        <div>
          <label className="label">Term (years)</label>
          <select
            className="input-field"
            value={form.term_years}
            onChange={(e) =>
              setForm((f) => ({ ...f, term_years: parseInt(e.target.value) }))
            }
          >
            <option value={10}>10 years</option>
            <option value={15}>15 years</option>
            <option value={20}>20 years</option>
            <option value={25}>25 years</option>
            <option value={30}>30 years</option>
          </select>
        </div>
      </div>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <button type="submit" disabled={loading} className="btn-primary w-full">
        {loading ? "Calculating..." : "Get Life Quote"}
      </button>
      {result && <QuoteResultCard result={result} />}
    </form>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function QuotesPage() {
  const [activeTab, setActiveTab] = useState<TabType>("auto");

  const tabs: { key: TabType; label: string; description: string }[] = [
    { key: "auto", label: "Auto Insurance", description: "Coverage for your vehicles" },
    { key: "home", label: "Home Insurance", description: "Protect your property" },
    { key: "life", label: "Life Insurance", description: "Secure your family's future" },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Insurance Quote Calculator</h1>
        <p className="text-gray-500 mt-1 text-sm">
          Get an instant premium estimate for InsureCo insurance products.
        </p>
      </div>

      {/* Tab selector */}
      <div className="card mb-6">
        <div className="flex">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex-1 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.key
                  ? "border-brand-red text-brand-red"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <p>{tab.label}</p>
              <p className="text-xs text-gray-400 mt-0.5 hidden sm:block">{tab.description}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="card p-6">
        {activeTab === "auto" && <AutoQuoteTab />}
        {activeTab === "home" && <HomeQuoteTab />}
        {activeTab === "life" && <LifeQuoteTab />}
      </div>
    </div>
  );
}
