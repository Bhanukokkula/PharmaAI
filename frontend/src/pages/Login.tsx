import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Pill } from "lucide-react";
import { useAuth } from "../lib/AuthContext";

const INPUT_CLASS =
  "mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100";

export function Login() {
  const [mode, setMode] = useState<"signin" | "create">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const { signIn, signInAsPersona, personas } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await signIn(email || "demo@pharmaai.local");
      navigate("/");
    } finally {
      setSubmitting(false);
    }
  }

  async function handlePersona(userId: number) {
    setSubmitting(true);
    try {
      await signInAsPersona(userId);
      navigate("/");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-12 sm:py-16">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <div className="flex flex-col items-center text-center">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600 text-white">
            <Pill className="h-5 w-5" />
          </span>
          <h1 className="mt-3 font-display text-2xl font-bold text-slate-900">
            {mode === "signin" ? "Sign in to PharmaAI" : "Create your account"}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {mode === "signin"
              ? "Welcome back — pick up your cart and recommendations."
              : "Mock sign-up — any details work, nothing is stored."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className={INPUT_CLASS}
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className={INPUT_CLASS}
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-full bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-700 disabled:opacity-50"
          >
            {submitting ? "Signing in…" : mode === "signin" ? "Sign in" : "Create account"}
          </button>
        </form>

        <button
          onClick={() => setMode((m) => (m === "signin" ? "create" : "signin"))}
          className="mt-3 w-full text-center text-sm text-teal-700 hover:underline"
        >
          {mode === "signin" ? "New here? Create an account" : "Already have an account? Sign in"}
        </button>

        <div className="my-6 flex items-center gap-3">
          <span className="h-px flex-1 bg-slate-200" />
          <span className="text-xs text-slate-400">or continue with</span>
          <span className="h-px flex-1 bg-slate-200" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            disabled
            className="cursor-not-allowed rounded-full border border-slate-200 py-2 text-sm text-slate-400"
          >
            Google
          </button>
          <button
            disabled
            className="cursor-not-allowed rounded-full border border-slate-200 py-2 text-sm text-slate-400"
          >
            Apple
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-slate-400">Social sign-in is visual only in this demo.</p>
      </div>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-display text-base font-semibold text-slate-900">
          Quick demo: shop as a sample customer
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          PharmaAI has no real accounts. Pick a seeded shopper persona to see personalized
          recommendations instantly.
        </p>
        <div className="mt-4 grid gap-2">
          {personas.map((p) => (
            <button
              key={p.id}
              onClick={() => handlePersona(p.id)}
              disabled={submitting}
              className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left hover:border-teal-600 hover:bg-teal-50 disabled:opacity-50"
            >
              <div>
                <p className="text-sm font-medium text-slate-900">{p.display_name}</p>
                <p className="text-xs text-slate-500">{p.segment_label}</p>
              </div>
              <ArrowRight className="h-4 w-4 text-slate-400" />
            </button>
          ))}
        </div>
      </div>

      <p className="mt-6 text-center text-xs text-slate-400">
        This is a mock session for demo purposes — there is no real authentication and no
        passwords are stored.
      </p>
    </div>
  );
}
