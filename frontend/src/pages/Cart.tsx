import { Link, useNavigate } from "react-router-dom";
import { Minus, Plus, ShieldCheck, ShoppingBag, Trash2 } from "lucide-react";
import { useCart } from "../lib/CartContext";
import { EmptyState } from "../components/EmptyState";
import { getCategoryStyle } from "../lib/categories";

const FREE_SHIPPING_THRESHOLD = 35;
const SHIPPING_COST = 4.99;

export function CartPage() {
  const { cart, loading, updateItem, removeItem } = useCart();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl space-y-4 px-4 py-8">
        <div className="h-8 w-40 animate-pulse rounded bg-slate-100" />
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-100" />
        ))}
      </div>
    );
  }

  if (cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8">
        <h1 className="font-display text-2xl font-bold text-slate-900">Your cart</h1>
        <div className="mt-6">
          <EmptyState
            icon={ShoppingBag}
            title="Your cart is empty"
            message="Browse OTC essentials and add a few items to get started."
            actionLabel="Browse products"
            actionTo="/shop"
          />
        </div>
      </div>
    );
  }

  const subtotal = cart.total;
  const shipping = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_COST;
  const total = subtotal + shipping;
  const remaining = FREE_SHIPPING_THRESHOLD - subtotal;

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <h1 className="font-display text-2xl font-bold text-slate-900">Your cart</h1>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          {cart.items.map((item) => {
            const style = getCategoryStyle(item.product.category);
            const Icon = style.icon;
            return (
              <div
                key={item.id}
                className="flex flex-wrap items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
              >
                <Link
                  to={`/products/${item.product.id}`}
                  className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-lg ${style.tint}`}
                >
                  <Icon className={`h-7 w-7 ${style.iconColor}`} aria-hidden="true" />
                </Link>
                <div className="min-w-0 flex-1">
                  <Link
                    to={`/products/${item.product.id}`}
                    className="font-display font-semibold text-slate-900 hover:text-teal-700"
                  >
                    {item.product.brand_name}
                  </Link>
                  <p className="text-sm text-slate-500">${item.product.price.toFixed(2)} each</p>
                </div>
                <div className="flex items-center rounded-full border border-slate-200">
                  <button
                    onClick={() => updateItem(item.id, Math.max(1, item.quantity - 1))}
                    aria-label="Decrease quantity"
                    className="flex h-8 w-8 items-center justify-center text-slate-500 hover:text-teal-700"
                  >
                    <Minus className="h-3.5 w-3.5" />
                  </button>
                  <span className="w-8 text-center text-sm font-medium">{item.quantity}</span>
                  <button
                    onClick={() => updateItem(item.id, item.quantity + 1)}
                    aria-label="Increase quantity"
                    className="flex h-8 w-8 items-center justify-center text-slate-500 hover:text-teal-700"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                </div>
                <p className="w-20 text-right font-display font-semibold text-slate-900">
                  ${(item.product.price * item.quantity).toFixed(2)}
                </p>
                <button
                  onClick={() => removeItem(item.id)}
                  aria-label={`Remove ${item.product.brand_name}`}
                  className="text-slate-400 hover:text-red-600"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            );
          })}

          <Link to="/shop" className="inline-block text-sm text-teal-700 hover:underline">
            ← Continue shopping
          </Link>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-display text-base font-semibold text-slate-900">Order summary</h2>
            <div className="mt-4 space-y-2 text-sm">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Shipping</span>
                <span>{shipping === 0 ? "Free" : `$${shipping.toFixed(2)}`}</span>
              </div>
              {remaining > 0 && (
                <p className="text-xs text-teal-700">
                  Add ${remaining.toFixed(2)} more to get free shipping.
                </p>
              )}
              <div className="flex justify-between border-t border-slate-200 pt-2 font-display text-base font-bold text-slate-900">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
            <button
              onClick={() => navigate("/checkout")}
              className="mt-4 w-full rounded-full bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
            >
              Proceed to checkout
            </button>
            <div className="mt-3 flex items-center justify-center gap-1.5 text-xs text-slate-400">
              <ShieldCheck className="h-3.5 w-3.5 text-teal-600" />
              Secure checkout — demo only, no payment processed.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
