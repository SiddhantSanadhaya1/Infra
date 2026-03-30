type IconType = "shield" | "file" | "clock" | "dollar";
type ColorType = "blue" | "orange" | "yellow" | "green" | "red";

interface StatsCardProps {
  label: string;
  value: number | string;
  icon: IconType;
  color: ColorType;
}

const ICON_PATHS: Record<IconType, string> = {
  shield:
    "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
  file: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  clock:
    "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z",
  dollar:
    "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

const COLOR_CLASSES: Record<
  ColorType,
  { bg: string; icon: string; value: string }
> = {
  blue: {
    bg: "bg-blue-50",
    icon: "text-blue-600",
    value: "text-blue-900",
  },
  orange: {
    bg: "bg-orange-50",
    icon: "text-orange-600",
    value: "text-orange-900",
  },
  yellow: {
    bg: "bg-yellow-50",
    icon: "text-yellow-600",
    value: "text-yellow-900",
  },
  green: {
    bg: "bg-green-50",
    icon: "text-green-600",
    value: "text-green-900",
  },
  red: {
    bg: "bg-red-50",
    icon: "text-red-600",
    value: "text-red-900",
  },
};

export default function StatsCard({ label, value, icon, color }: StatsCardProps) {
  const colors = COLOR_CLASSES[color];
  const iconPath = ICON_PATHS[icon];

  return (
    <div className={`card p-5 flex items-center gap-4 ${colors.bg}`}>
      <div className={`p-3 rounded-full bg-white shadow-sm ${colors.icon}`}>
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d={iconPath}
          />
        </svg>
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{label}</p>
        <p className={`text-2xl font-bold ${colors.value}`}>{value}</p>
      </div>
    </div>
  );
}
