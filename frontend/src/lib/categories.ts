import { Droplet, Leaf, Package, Pill, Thermometer, Wind, type LucideIcon } from "lucide-react";

export interface CategoryStyle {
  icon: LucideIcon;
  badge: string;
  tint: string;
  iconColor: string;
}

export const CATEGORIES = ["Pain Relief", "Allergy", "Cold & Flu", "Digestive", "Vitamins & Supplements"];

const STYLES: Record<string, CategoryStyle> = {
  "Pain Relief": { icon: Pill, badge: "bg-rose-100 text-rose-700", tint: "bg-rose-50", iconColor: "text-rose-500" },
  Allergy: { icon: Wind, badge: "bg-amber-100 text-amber-700", tint: "bg-amber-50", iconColor: "text-amber-500" },
  "Cold & Flu": { icon: Thermometer, badge: "bg-sky-100 text-sky-700", tint: "bg-sky-50", iconColor: "text-sky-500" },
  Digestive: { icon: Droplet, badge: "bg-lime-100 text-lime-700", tint: "bg-lime-50", iconColor: "text-lime-600" },
  "Vitamins & Supplements": {
    icon: Leaf,
    badge: "bg-violet-100 text-violet-700",
    tint: "bg-violet-50",
    iconColor: "text-violet-500",
  },
};

const DEFAULT_STYLE: CategoryStyle = {
  icon: Package,
  badge: "bg-slate-100 text-slate-700",
  tint: "bg-slate-50",
  iconColor: "text-slate-400",
};

export function getCategoryStyle(category: string): CategoryStyle {
  return STYLES[category] ?? DEFAULT_STYLE;
}
