interface ClaimStatusBadgeProps {
  status: string;
}

const STATUS_CONFIG: Record<
  string,
  { label: string; className: string }
> = {
  SUBMITTED: {
    label: "Submitted",
    className: "bg-blue-100 text-blue-700 border-blue-200",
  },
  UNDER_REVIEW: {
    label: "Under Review",
    className: "bg-purple-100 text-purple-700 border-purple-200",
  },
  APPROVED: {
    label: "Approved",
    className: "bg-green-100 text-green-700 border-green-200",
  },
  REJECTED: {
    label: "Rejected",
    className: "bg-red-100 text-red-700 border-red-200",
  },
  PAID: {
    label: "Paid",
    className: "bg-emerald-100 text-emerald-700 border-emerald-200",
  },
};

export default function ClaimStatusBadge({ status }: ClaimStatusBadgeProps) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    className: "bg-gray-100 text-gray-600 border-gray-200",
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded border text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}
