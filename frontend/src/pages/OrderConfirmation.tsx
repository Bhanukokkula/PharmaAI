import { Link, Navigate, useLocation } from "react-router-dom";
import { CheckCircle2 } from "lucide-react";
import type { Order } from "../lib/api";
import { StepIndicator } from "../components/StepIndicator";
import type { ShippingInfo } from "./Checkout";

const CHECKOUT_STEPS = ["Shipping", "Payment", "Review", "Confirmation"];

export function OrderConfirmation() {
  const location = useLocation();
  const state = location.state as { order?: Order; shipping?: ShippingInfo } | null;
  const order = state?.order;
  const shipping = state?.shipping;

  if (!order) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 px-4 py-8">
      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <StepIndicator steps={CHECKOUT_STEPS} current={4} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-teal-50 text-teal-600">
          <CheckCircle2 className="h-7 w-7" />
        </span>
        <h1 className="mt-4 font-display text-2xl font-bold text-slate-900">Order placed!</h1>
        <p className="mt-1 text-slate-500">
          Order #{order.id} — ${order.total.toFixed(2)}
        </p>
        <p className="mt-3 text-sm text-slate-400">
          This is a demo order — no payment was processed and nothing will ship.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {shipping && (
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-display text-sm font-semibold text-slate-900">Shipped to</h2>
            <p className="mt-2 text-sm text-slate-600">
              {shipping.fullName}
              <br />
              {shipping.address}
              <br />
              {shipping.city}, {shipping.state} {shipping.zip}
            </p>
          </div>
        )}

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="font-display text-sm font-semibold text-slate-900">Order summary</h2>
          <ul className="mt-2 divide-y divide-slate-100 text-sm">
            {order.items.map((item) => (
              <li key={item.product_id} className="flex justify-between gap-2 py-2 text-slate-600">
                <span className="truncate">
                  {item.product.brand_name} × {item.quantity}
                </span>
                <span className="shrink-0">${(item.unit_price * item.quantity).toFixed(2)}</span>
              </li>
            ))}
          </ul>
          <div className="mt-2 flex justify-between border-t border-slate-200 pt-2 font-display text-base font-bold text-slate-900">
            <span>Total</span>
            <span>${order.total.toFixed(2)}</span>
          </div>
        </div>
      </div>

      <div className="text-center">
        <Link
          to="/shop"
          className="inline-block rounded-full bg-teal-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
        >
          Continue shopping
        </Link>
      </div>
    </div>
  );
}
