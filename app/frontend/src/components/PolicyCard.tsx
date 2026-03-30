import { Policy } from "@/services/api";

interface PolicyCardProps {
  policy: Policy;
}

const TYPE_LABELS: Record<string, string> = {
  AUTO: "Auto Insurance",
  HOME: "Home Insurance",
  LIFE: "Life Insurance",
  COMMERCIAL: "Commercial Insurance",
};

const TYPE_ICONS: Record<string, string> = {
  AUTO: "🚗",
  HOME: "🏠",
  LIFE: "❤️",
  COMMERCIAL: "🏢",
};

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: "bg-green-100 text-green-700 border-green-200",
  EXPIRED: "bg-gray-100 text-gray-600 border-gray-200",
  CANCELLED: "bg-red-100 text-red-700 border-red-200",
  PENDING: "bg-yellow-100 text-yellow-700 border-yellow-200",
};

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

function isExpiringSoon(endDate: string): boolean {
  const end = new Date(endDate);
  const now = new Date();
  const diffDays = (end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays > 0 && diffDays <= 30;
}

export default function PolicyCard({ policy }: PolicyCardProps) {
  const expiringSoon = isExpiringSoon(policy.end_date);
  const premiumMonthly = parseFloat(String(policy.premium_amount)) / 12;
  const coverage = parseFloat(String(policy.coverage_amount));

  return (
    <div className="card p-5 hover:shadow-md transition-shadow flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span className="text-2xl" role="img" aria-label={policy.policy_type}>
            {TYPE_ICONS[policy.policy_type] ?? "📋"}
          </span>
          <div>
            <p className="font-semibold text-gray-900 text-sm">
              {TYPE_LABELS[policy.policy_type] ?? policy.policy_type}
            </p>
            <p className="font-mono text-xs text-gray-400">{policy.policy_number}</p>
          </div>
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${
            STATUS_COLORS[policy.status] ?? "bg-gray-100 text-gray-600"
          }`}
        >
          {policy.status}
        </span>
      </div>

      {/* Coverage & premium */}
      <div className="grid grid-cols-2 gap-3 bg-gray-50 rounded-md p-3">
        <div>
          <p className="text-xs text-gray-400">Coverage Amount</p>
          <p className="font-bold text-gray-900">{formatCurrency(coverage)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400">Monthly Premium</p>
          <p className="font-bold text-gray-900">{formatCurrency(premiumMonthly)}</p>
        </div>
      </div>

      {/* Dates */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Effective: {formatDate(policy.start_date)}</span>
        <span
          className={expiringSoon ? "text-orange-600 font-medium" : ""}
        >
          Expires: {formatDate(policy.end_date)}
          {expiringSoon && " (soon)"}
        </span>
      </div>

      {expiringSoon && (
        <div className="bg-orange-50 border border-orange-200 text-orange-700 rounded px-3 py-1.5 text-xs">
          This policy expires within 30 days. Contact InsureCo to renew.
        </div>
      )}
    </div>
  );
}
