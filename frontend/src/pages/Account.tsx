import { useEffect, useState } from "react";
import { PackageOpen, Sparkles, UserRound } from "lucide-react";
import { api, type Order } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { EmptyState } from "../components/EmptyState";

export function Account() {
  const { user, isSignedIn, segmentLabel, signOut, loading } = useAuth();
  const [orders, setOrders] = useState<Order[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!isSignedIn) return;
    api
      .listOrders()
      .then(setOrders)
      .catch(() => setError(true));
  }, [isSignedIn]);

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl space-y-4 px-4 py-8">
        <div className="h-8 w-40 animate-pulse rounded bg-slate-100" />
        <div className="h-20 animate-pulse rounded-xl bg-slate-100" />
      </div>
    );
  }

  if (!isSignedIn || !user) {
    return (
      <div className="mx-auto max-w-md px-4 py-12">
        <EmptyState
          icon={UserRound}
          title="You're not signed in"
          message="Sign in to view your account, order history, and personalized recommendations."
          actionLabel="Sign in"
          actionTo="/login"
        />
      </div>
    );
  }

  const initial = user.display_name.trim().charAt(0).toUpperCase();

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <h1 className="font-display text-2xl font-bold text-slate-900">Your account</h1>

      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-100 text-lg font-semibold text-teal-700">
            {initial}
          </span>
          <div>
            <p className="font-display font-semibold text-slate-900">{user.display_name}</p>
            <p className="text-sm text-slate-500">@{user.username}</p>
          </div>
        </div>
        <button
          onClick={() => void signOut()}
          className="rounded-full border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 hover:border-teal-600 hover:text-teal-700"
        >
          Sign out
        </button>
      </div>

      {segmentLabel && (
        <div className="flex items-start gap-3 rounded-xl border border-teal-100 bg-teal-50 p-4">
          <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-teal-600" />
          <p className="text-sm text-teal-800">
            Shopping as a <span className="font-semibold">{segmentLabel}</span> persona —
            recommendations on the home page are tuned for this kind of shopper.
          </p>
        </div>
      )}

      <div>
        <h2 className="font-display text-lg font-semibold text-slate-900">Order history</h2>

        {error && <p className="mt-2 text-red-600">Could not load order history.</p>}

        {!error && orders === null && (
          <div className="mt-3 space-y-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="h-20 animate-pulse rounded-xl bg-slate-100" />
            ))}
          </div>
        )}

        {orders && orders.length === 0 && (
          <div className="mt-3">
            <EmptyState
              icon={PackageOpen}
              title="No orders yet"
              message="Your demo orders will show up here once you check out."
              actionLabel="Browse products"
              actionTo="/shop"
            />
          </div>
        )}

        {orders && orders.length > 0 && (
          <div className="mt-3 space-y-3">
            {orders.map((order) => (
              <div key={order.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <p className="font-display font-semibold text-slate-900">Order #{order.id}</p>
                  <p className="text-sm text-slate-500">
                    {new Date(order.created_at).toLocaleDateString()}
                  </p>
                </div>
                <ul className="mt-2 divide-y divide-slate-100 text-sm">
                  {order.items.map((item) => (
                    <li key={item.product_id} className="flex justify-between gap-2 py-1.5 text-slate-600">
                      <span className="truncate">
                        {item.product.brand_name} × {item.quantity}
                      </span>
                      <span className="shrink-0">${(item.unit_price * item.quantity).toFixed(2)}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 text-sm font-semibold text-slate-900">
                  <span>Total</span>
                  <span>${order.total.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
