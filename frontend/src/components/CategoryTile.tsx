import { Link } from "react-router-dom";
import { getCategoryStyle } from "../lib/categories";

export function CategoryTile({ category }: { category: string }) {
  const style = getCategoryStyle(category);
  const Icon = style.icon;

  return (
    <Link
      to={`/shop?category=${encodeURIComponent(category)}`}
      className="group flex flex-col items-center gap-3 rounded-xl border border-slate-200 bg-white p-6 text-center shadow-sm transition-shadow hover:shadow-md"
    >
      <span className={`flex h-12 w-12 items-center justify-center rounded-full ${style.tint}`}>
        <Icon className={`h-6 w-6 ${style.iconColor}`} aria-hidden="true" />
      </span>
      <span className="font-display text-sm font-semibold text-slate-900 group-hover:text-teal-700">{category}</span>
    </Link>
  );
}
