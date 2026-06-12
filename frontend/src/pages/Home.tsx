import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BadgeCheck,
  Leaf,
  Lock,
  Pill,
  RotateCcw,
  Search,
  ShoppingBag,
  Sparkles,
  Truck,
  Wind,
} from "lucide-react";
import { api, type Product, type RecommendationResponse } from "../lib/api";
import { ProductCard } from "../components/ProductCard";
import { ProductCardSkeletonGrid } from "../components/Skeletons";
import { CategoryTile } from "../components/CategoryTile";
import { CATEGORIES } from "../lib/categories";

const TRUST_POINTS = [
  {
    icon: BadgeCheck,
    title: "FDA-sourced product info",
    text: "Purpose, ingredients, and warnings come straight from openFDA drug labels.",
  },
  {
    icon: Truck,
    title: "Free shipping over $35",
    text: "Everyday OTC essentials, delivered — no membership required.",
  },
  {
    icon: RotateCcw,
    title: "Easy returns",
    text: "Changed your mind? Unopened items can be returned within 30 days.",
  },
  {
    icon: Lock,
    title: "Secure checkout",
    text: "A familiar, guarded checkout flow — this demo doesn't process real payments.",
  },
];

const HOW_IT_WORKS = [
  {
    icon: Search,
    title: "Browse by need",
    text: "Search or shop by category — pain relief, allergy, cold & flu, digestive, vitamins.",
  },
  {
    icon: Sparkles,
    title: "See what fits",
    text: "Get picks framed as \"popular with similar shoppers\" — never a diagnosis or dosage suggestion.",
  },
  {
    icon: ShoppingBag,
    title: "Checkout with confidence",
    text: "A clear, guided checkout. Demo orders only — nothing ships, nothing is charged.",
  },
];

export function Home() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [recError, setRecError] = useState(false);
  const [featured, setFeatured] = useState<Product[]>([]);
  const [featuredError, setFeaturedError] = useState(false);

  useEffect(() => {
    api
      .getRecommendations(6)
      .then(setRecommendations)
      .catch(() => setRecError(true));
    api
      .listProducts({ limit: 8 })
      .then((res) => setFeatured(res.items))
      .catch(() => setFeaturedError(true));
  }, []);

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    const trimmed = search.trim();
    navigate(trimmed ? `/shop?q=${encodeURIComponent(trimmed)}` : "/shop");
  }

  return (
    <div>
      {/* Hero */}
      <section className="mx-auto max-w-6xl px-4 py-12 sm:py-16">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <h1 className="font-display text-4xl font-extrabold leading-tight text-slate-900 sm:text-5xl">
              Everyday OTC care, made simple.
            </h1>
            <p className="mt-4 max-w-md text-lg text-slate-600">
              Pain relief, allergy, cold &amp; flu, digestive, and vitamins — browse trusted OTC
              essentials with FDA-sourced product info, all in one calm, clutter-free shop.
            </p>

            <form onSubmit={handleSearch} className="mt-6 flex max-w-md gap-2">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search allergy relief, ibuprofen…"
                  aria-label="Search products"
                  className="w-full rounded-full border border-slate-200 bg-white py-3 pl-10 pr-4 text-sm text-slate-700 placeholder:text-slate-400 shadow-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
                />
              </div>
              <button
                type="submit"
                className="flex items-center gap-1 rounded-full bg-teal-600 px-5 py-3 text-sm font-semibold text-white hover:bg-teal-700"
              >
                Search
              </button>
            </form>

            <div className="mt-6 flex flex-wrap gap-2">
              {CATEGORIES.map((c) => (
                <Link
                  key={c}
                  to={`/shop?category=${encodeURIComponent(c)}`}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 hover:border-teal-600 hover:text-teal-700"
                >
                  {c}
                </Link>
              ))}
            </div>
          </div>

          <div className="relative hidden lg:block">
            <div className="absolute -right-6 -top-8 h-40 w-40 rounded-full bg-teal-100 blur-3xl" aria-hidden="true" />
            <div className="absolute -bottom-10 -left-10 h-44 w-44 rounded-full bg-amber-100 blur-3xl" aria-hidden="true" />
            <div className="relative grid grid-cols-2 gap-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="col-span-2 rounded-2xl bg-teal-50 p-5">
                <Pill className="h-8 w-8 text-teal-600" />
                <p className="mt-3 font-display text-base font-semibold text-slate-900">Pain Relief</p>
                <p className="text-sm text-slate-500">Ibuprofen, acetaminophen &amp; more</p>
              </div>
              <div className="rounded-2xl bg-amber-50 p-5">
                <Wind className="h-8 w-8 text-amber-500" />
                <p className="mt-3 font-display text-base font-semibold text-slate-900">Allergy</p>
              </div>
              <div className="rounded-2xl bg-violet-50 p-5">
                <Leaf className="h-8 w-8 text-violet-500" />
                <p className="mt-3 font-display text-base font-semibold text-slate-900">Vitamins</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Category tiles */}
      <section className="mx-auto max-w-6xl px-4 py-8">
        <h2 className="font-display text-2xl font-bold text-slate-900">Shop by category</h2>
        <div className="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          {CATEGORIES.map((c) => (
            <CategoryTile key={c} category={c} />
          ))}
        </div>
      </section>

      {/* Recommended for you */}
      <section className="mx-auto max-w-6xl px-4 py-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-2xl font-bold text-slate-900">Recommended for you</h2>
            <p className="mt-1 text-sm text-slate-500">
              Popular with shoppers like you — not medical advice.
            </p>
          </div>
          <Link to="/shop" className="hidden items-center gap-1 text-sm font-medium text-teal-700 hover:underline sm:flex">
            Browse all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {recError && <p className="mt-4 text-red-600">Could not load recommendations. Is the API running?</p>}

        {!recError && !recommendations && <div className="mt-5"><ProductCardSkeletonGrid count={3} /></div>}

        {recommendations && recommendations.items.length > 0 && (
          <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {recommendations.items.slice(0, 6).map((item) => (
              <div key={item.product.id}>
                <ProductCard product={item.product} />
                <p className="mt-1.5 px-1 text-xs text-slate-400">{item.reason}</p>
              </div>
            ))}
          </div>
        )}

        {recommendations && recommendations.items.length === 0 && (
          <p className="mt-4 text-slate-500">No recommendations yet — browse a few products to get started.</p>
        )}
      </section>

      {/* Featured / bestsellers */}
      <section className="mx-auto max-w-6xl px-4 py-8">
        <h2 className="font-display text-2xl font-bold text-slate-900">Featured essentials</h2>
        {featuredError && <p className="mt-4 text-red-600">Could not load products. Is the API running?</p>}
        {!featuredError && featured.length === 0 && <div className="mt-5"><ProductCardSkeletonGrid count={4} /></div>}
        {featured.length > 0 && (
          <div className="mt-5 flex gap-4 overflow-x-auto pb-2">
            {featured.map((p) => (
              <div key={p.id} className="w-64 shrink-0">
                <ProductCard product={p} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Trust band */}
      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 sm:grid-cols-2 lg:grid-cols-4">
          {TRUST_POINTS.map(({ icon: Icon, title, text }) => (
            <div key={title} className="flex flex-col items-start gap-2">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-teal-50 text-teal-600">
                <Icon className="h-5 w-5" />
              </span>
              <h3 className="font-display text-sm font-semibold text-slate-900">{title}</h3>
              <p className="text-sm text-slate-500">{text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-6xl px-4 py-12">
        <h2 className="font-display text-2xl font-bold text-slate-900">How PharmaAI works</h2>
        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          {HOW_IT_WORKS.map(({ icon: Icon, title, text }, i) => (
            <div key={title} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-teal-600 text-sm font-semibold text-white">
                  {i + 1}
                </span>
                <Icon className="h-5 w-5 text-teal-600" />
              </div>
              <h3 className="mt-3 font-display text-base font-semibold text-slate-900">{title}</h3>
              <p className="mt-1 text-sm text-slate-500">{text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
