import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";
import type { Product } from "../lib/api";
import { useCart } from "../lib/CartContext";
import { getCategoryStyle } from "../lib/categories";

export function CategoryBadge({ category }: { category: string }) {
  const style = getCategoryStyle(category);
  return <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${style.badge}`}>{category}</span>;
}

export function ProductCard({ product }: { product: Product }) {
  const { addToCart } = useCart();
  const [adding, setAdding] = useState(false);
  const style = getCategoryStyle(product.category);
  const Icon = style.icon;

  async function handleAdd() {
    setAdding(true);
    try {
      await addToCart(product.id, 1);
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md">
      <Link to={`/products/${product.id}`} className={`flex h-32 items-center justify-center ${style.tint}`}>
        <Icon className={`h-10 w-10 ${style.iconColor}`} aria-hidden="true" />
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <CategoryBadge category={product.category} />
        <Link
          to={`/products/${product.id}`}
          className="mt-2 line-clamp-2 font-display font-semibold text-slate-900 group-hover:text-teal-700"
        >
          {product.brand_name}
        </Link>
        {product.generic_name && <p className="text-xs text-slate-500">{product.generic_name}</p>}
        {product.purpose && <p className="mt-2 line-clamp-2 text-sm text-slate-600">{product.purpose}</p>}
        <div className="mt-3 flex items-center justify-between pt-1">
          <span className="font-display text-lg font-bold text-slate-900">${product.price.toFixed(2)}</span>
          <button
            onClick={handleAdd}
            disabled={adding}
            className="flex items-center gap-1 rounded-full bg-teal-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
          >
            <Plus className="h-3.5 w-3.5" />
            {adding ? "Adding…" : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}
