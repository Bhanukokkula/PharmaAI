import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Lock, ShieldCheck } from "lucide-react";
import { api } from "../lib/api";
import { useCart } from "../lib/CartContext";
import { StepIndicator } from "../components/StepIndicator";

const STEPS = ["Shipping", "Payment", "Review"];
const FREE_SHIPPING_THRESHOLD = 35;
const SHIPPING_COST = 4.99;

const INPUT_CLASS =
  "mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100";

export interface ShippingInfo {
  fullName: string;
  address: string;
  city: string;
  state: string;
  zip: string;
}

interface PaymentInfo {
  cardName: string;
  cardNumber: string;
  expiry: string;
  cvc: string;
}

export function Checkout() {
  const { cart, refresh } = useCart();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shipping, setShipping] = useState<ShippingInfo>({
    fullName: "",
    address: "",
    city: "",
    state: "",
    zip: "",
  });
  const [payment, setPayment] = useState<PaymentInfo>({
    cardName: "",
    cardNumber: "",
    expiry: "",
    cvc: "",
  });

  if (cart.items.length === 0) {
    return <Navigate to="/cart" replace />;
  }

  const subtotal = cart.total;
  const shippingCost = subtotal >= FREE_SHIPPING_THRESHOLD ? 0 : SHIPPING_COST;
  const total = subtotal + shippingCost;

  function updateShipping(field: keyof ShippingInfo, value: string) {
    setShipping((prev) => ({ ...prev, [field]: value }));
  }

  function updatePayment(field: keyof PaymentInfo, value: string) {
    setPayment((prev) => ({ ...prev, [field]: value }));
  }

  function handleShippingSubmit(e: FormEvent) {
    e.preventDefault();
    setStep(2);
  }

  function handlePaymentSubmit(e: FormEvent) {
    e.preventDefault();
    setStep(3);
  }

  async function handlePlaceOrder() {
    setPlacing(true);
    setError(null);
    try {
      const order = await api.checkout();
      await refresh();
      navigate("/order-confirmation", { state: { order, shipping } });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not place order. Please try again.");
    } finally {
      setPlacing(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <h1 className="font-display text-2xl font-bold text-slate-900">Checkout</h1>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
        <StepIndicator steps={STEPS} current={step} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {step === 1 && (
            <form
              onSubmit={handleShippingSubmit}
              className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <h2 className="font-display text-lg font-semibold text-slate-900">Shipping address</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="fullName" className="block text-sm font-medium text-slate-700">
                    Full name
                  </label>
                  <input
                    id="fullName"
                    required
                    value={shipping.fullName}
                    onChange={(e) => updateShipping("fullName", e.target.value)}
                    placeholder="Jordan Smith"
                    className={INPUT_CLASS}
                  />
                </div>
                <div className="sm:col-span-2">
                  <label htmlFor="address" className="block text-sm font-medium text-slate-700">
                    Street address
                  </label>
                  <input
                    id="address"
                    required
                    value={shipping.address}
                    onChange={(e) => updateShipping("address", e.target.value)}
                    placeholder="123 Main St, Apt 4B"
                    className={INPUT_CLASS}
                  />
                </div>
                <div>
                  <label htmlFor="city" className="block text-sm font-medium text-slate-700">
                    City
                  </label>
                  <input
                    id="city"
                    required
                    value={shipping.city}
                    onChange={(e) => updateShipping("city", e.target.value)}
                    placeholder="Springfield"
                    className={INPUT_CLASS}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="state" className="block text-sm font-medium text-slate-700">
                      State
                    </label>
                    <input
                      id="state"
                      required
                      value={shipping.state}
                      onChange={(e) => updateShipping("state", e.target.value)}
                      placeholder="CA"
                      className={INPUT_CLASS}
                    />
                  </div>
                  <div>
                    <label htmlFor="zip" className="block text-sm font-medium text-slate-700">
                      ZIP code
                    </label>
                    <input
                      id="zip"
                      required
                      value={shipping.zip}
                      onChange={(e) => updateShipping("zip", e.target.value)}
                      placeholder="94016"
                      className={INPUT_CLASS}
                    />
                  </div>
                </div>
              </div>
              <button
                type="submit"
                className="w-full rounded-full bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
              >
                Continue to payment
              </button>
            </form>
          )}

          {step === 2 && (
            <form
              onSubmit={handlePaymentSubmit}
              className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-teal-600" />
                <h2 className="font-display text-lg font-semibold text-slate-900">Payment details</h2>
              </div>
              <p className="rounded-lg bg-teal-50 px-3 py-2 text-xs text-teal-800">
                Demo checkout — this form is for illustration only. No real payment is processed and
                no card details are stored.
              </p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="cardName" className="block text-sm font-medium text-slate-700">
                    Name on card
                  </label>
                  <input
                    id="cardName"
                    required
                    value={payment.cardName}
                    onChange={(e) => updatePayment("cardName", e.target.value)}
                    placeholder="Jordan Smith"
                    className={INPUT_CLASS}
                  />
                </div>
                <div className="sm:col-span-2">
                  <label htmlFor="cardNumber" className="block text-sm font-medium text-slate-700">
                    Card number
                  </label>
                  <input
                    id="cardNumber"
                    required
                    inputMode="numeric"
                    value={payment.cardNumber}
                    onChange={(e) => updatePayment("cardNumber", e.target.value)}
                    placeholder="4242 4242 4242 4242"
                    className={INPUT_CLASS}
                  />
                </div>
                <div>
                  <label htmlFor="expiry" className="block text-sm font-medium text-slate-700">
                    Expiry
                  </label>
                  <input
                    id="expiry"
                    required
                    value={payment.expiry}
                    onChange={(e) => updatePayment("expiry", e.target.value)}
                    placeholder="MM/YY"
                    className={INPUT_CLASS}
                  />
                </div>
                <div>
                  <label htmlFor="cvc" className="block text-sm font-medium text-slate-700">
                    CVC
                  </label>
                  <input
                    id="cvc"
                    required
                    inputMode="numeric"
                    value={payment.cvc}
                    onChange={(e) => updatePayment("cvc", e.target.value)}
                    placeholder="123"
                    className={INPUT_CLASS}
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="rounded-full border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:border-teal-600 hover:text-teal-700"
                >
                  Back
                </button>
                <button
                  type="submit"
                  className="flex-1 rounded-full bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
                >
                  Review order
                </button>
              </div>
            </form>
          )}

          {step === 3 && (
            <div className="space-y-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="font-display text-lg font-semibold text-slate-900">Review your order</h2>

              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-700">Shipping to</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    {shipping.fullName}
                    <br />
                    {shipping.address}
                    <br />
                    {shipping.city}, {shipping.state} {shipping.zip}
                  </p>
                </div>
                <div className="rounded-lg border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-700">Payment</h3>
                  <p className="mt-1 text-sm text-slate-600">
                    Card ending in {payment.cardNumber.replace(/\s/g, "").slice(-4) || "----"}
                  </p>
                  <p className="mt-1 text-xs text-slate-400">Demo only — no charge will be made.</p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-700">Items</h3>
                <ul className="mt-2 divide-y divide-slate-100 text-sm">
                  {cart.items.map((item) => (
                    <li key={item.id} className="flex justify-between py-2 text-slate-600">
                      <span>
                        {item.product.brand_name} × {item.quantity}
                      </span>
                      <span>${(item.product.price * item.quantity).toFixed(2)}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {error && <p className="text-sm text-red-600">{error}</p>}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={placing}
                  className="rounded-full border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 hover:border-teal-600 hover:text-teal-700 disabled:opacity-50"
                >
                  Back
                </button>
                <button
                  type="button"
                  onClick={handlePlaceOrder}
                  disabled={placing}
                  className="flex-1 rounded-full bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  {placing ? "Placing order…" : "Place order"}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="font-display text-base font-semibold text-slate-900">Order summary</h2>
            <ul className="mt-3 space-y-2 text-sm text-slate-600">
              {cart.items.map((item) => (
                <li key={item.id} className="flex justify-between gap-2">
                  <span className="truncate">
                    {item.product.brand_name} × {item.quantity}
                  </span>
                  <span className="shrink-0">${(item.product.price * item.quantity).toFixed(2)}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 space-y-2 border-t border-slate-200 pt-3 text-sm">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Shipping</span>
                <span>{shippingCost === 0 ? "Free" : `$${shippingCost.toFixed(2)}`}</span>
              </div>
              <div className="flex justify-between border-t border-slate-200 pt-2 font-display text-base font-bold text-slate-900">
                <span>Total</span>
                <span>${total.toFixed(2)}</span>
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
              <ShieldCheck className="h-4 w-4 shrink-0 text-teal-600" />
              Secure demo checkout — no real payment is processed.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
