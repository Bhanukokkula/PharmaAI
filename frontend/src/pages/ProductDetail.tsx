import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Check, ChevronLeft, Minus, Plus } from "lucide-react";
import { api, type Product, type RecommendationResponse } from "../lib/api";
import { useCart } from "../lib/CartContext";
import { CategoryBadge, ProductCard } from "../components/ProductCard";
import { WarningsPanel } from "../components/WarningsPanel";
import { NonAdviceNote } from "../components/Disclaimer";
import { ProductCardSkeletonGrid } from "../components/Skeletons";
import { getCategoryStyle } from "../lib/categories";

function InfoSection({ title, text }: { title: string; text: string | null }) {
  if (!text) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="font-display text-sm font-semibold text-slate-700">{title}</h2>
      <p className="mt-1 whitespace-pre-line text-sm text-slate-600">{text}</p>
    </div>
  );
}

export function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [added, setAdded] = useState(false);
  const [related, setRelated] = useState<RecommendationResponse | null>(null);
  const { addToCart } = useCart();

  useEffect(() => {
    if (!id) return;
    setProduct(null);
    setError(false);
    api
      .getProduct(Number(id))
      .then(setProduct)
      .catch(() => setError(true));
  }, [id]);

  useEffect(() => {
    api
      .getRecommendations(4)
      .then(setRelated)
      .catch(() => setRelated(null));
  }, [id]);

  async function handleAdd() {
    if (!product) return;
    await addToCart(product.id, quantity);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  if (error) {
    return (
      <div className="mx-auto max-w-6xl space-y-4 px-4 py-8">
        <p className="text-red-600">Product not found.</p>
        <Link to="/shop" className="inline-flex items-center gap-1 text-teal-700 hover:underline">
          <ChevronLeft className="h-4 w-4" /> Back to shop
        </Link>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
        <div className="h-64 animate-pulse rounded-xl bg-slate-100" />
        <ProductCardSkeletonGrid count={3} />
      </div>
    );
  }

  const style = getCategoryStyle(product.category);
  const Icon = style.icon;
  const relatedItems = related?.items.filter((item) => item.product.id !== product.id) ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-8">
      <Link to="/shop" className="inline-flex items-center gap-1 text-sm text-teal-700 hover:underline">
        <ChevronLeft className="h-4 w-4" /> Back to shop
      </Link>

      <div className="grid gap-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:grid-cols-2">
        <div className={`flex h-56 items-center justify-center rounded-xl ${style.tint}`}>
          <Icon className={`h-20 w-20 ${style.iconColor}`} aria-hidden="true" />
        </div>

        <div className="flex flex-col">
          <CategoryBadge category={product.category} />
          <h1 className="mt-2 font-display text-2xl font-bold text-slate-900">{product.brand_name}</h1>
          {product.generic_name && <p className="text-slate-500">{product.generic_name}</p>}
          <p className="mt-3 font-display text-2xl font-bold text-slate-900">${product.price.toFixed(2)}</p>

          <div className="mt-6 flex items-center gap-3">
            <div className="flex items-center rounded-full border border-slate-200">
              <button
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                aria-label="Decrease quantity"
                className="flex h-10 w-10 items-center justify-center text-slate-500 hover:text-teal-700"
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-8 text-center text-sm font-medium">{quantity}</span>
              <button
                onClick={() => setQuantity((q) => q + 1)}
                aria-label="Increase quantity"
                className="flex h-10 w-10 items-center justify-center text-slate-500 hover:text-teal-700"
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
            <button
              onClick={handleAdd}
              className="flex items-center gap-2 rounded-full bg-teal-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
            >
              {added ? (
                <>
                  <Check className="h-4 w-4" /> Added to cart
                </>
              ) : (
                "Add to cart"
              )}
            </button>
          </div>

          <NonAdviceNote className="mt-4" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <InfoSection title="Purpose" text={product.purpose} />
        <InfoSection title="Active ingredient" text={product.active_ingredient} />
        <InfoSection title="Directions" text={product.dosage_and_administration} />
        {product.warnings && <WarningsPanel text={product.warnings} />}
      </div>

      {relatedItems.length > 0 && (
        <div>
          <h2 className="font-display text-xl font-bold text-slate-900">You might also like</h2>
          <p className="mt-1 text-sm text-slate-500">Popular with similar shoppers — not medical advice.</p>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {relatedItems.slice(0, 4).map((item) => (
              <ProductCard key={item.product.id} product={item.product} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
