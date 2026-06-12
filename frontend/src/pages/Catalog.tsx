import { useEffect, useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { PackageSearch, Search } from "lucide-react";
import { api, type Product } from "../lib/api";
import { ProductCard } from "../components/ProductCard";
import { ProductCardSkeletonGrid } from "../components/Skeletons";
import { EmptyState } from "../components/EmptyState";
import { CATEGORIES } from "../lib/categories";

const PAGE_SIZE = 12;

type SortOption = "relevance" | "price-asc" | "price-desc";

export function Catalog() {
  const [searchParams, setSearchParams] = useSearchParams();
  const category = searchParams.get("category");
  const query = searchParams.get("q") ?? "";

  const [searchInput, setSearchInput] = useState(query);
  const [sort, setSort] = useState<SortOption>("relevance");
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    setSearchInput(query);
  }, [query]);

  useEffect(() => {
    setOffset(0);
    setProducts([]);
  }, [category, query]);

  useEffect(() => {
    setLoading(true);
    setError(false);
    api
      .listProducts({ category: category ?? undefined, q: query || undefined, limit: PAGE_SIZE, offset })
      .then((res) => {
        setProducts((prev) => (offset === 0 ? res.items : [...prev, ...res.items]));
        setTotal(res.total);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [category, query, offset]);

  function handleCategoryChange(next: string | null) {
    const params = new URLSearchParams(searchParams);
    if (next) {
      params.set("category", next);
    } else {
      params.delete("category");
    }
    setSearchParams(params);
  }

  function handleSearchSubmit(e: FormEvent) {
    e.preventDefault();
    const params = new URLSearchParams(searchParams);
    const trimmed = searchInput.trim();
    if (trimmed) {
      params.set("q", trimmed);
    } else {
      params.delete("q");
    }
    setSearchParams(params);
  }

  const canLoadMore = products.length < total;

  const sortedProducts = [...products].sort((a, b) => {
    if (sort === "price-asc") return a.price - b.price;
    if (sort === "price-desc") return b.price - a.price;
    return 0;
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div>
        <h1 className="font-display text-2xl font-bold text-slate-900">{category ?? "Shop all products"}</h1>
        <p className="mt-1 text-sm text-slate-500">
          {total > 0 ? `${total} product${total === 1 ? "" : "s"}` : "Browse OTC essentials"}
          {query ? ` matching "${query}"` : ""}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => handleCategoryChange(null)}
          className={`rounded-full px-3 py-1.5 text-sm font-medium ${
            category === null ? "bg-teal-600 text-white" : "border border-slate-200 bg-white text-slate-600 hover:border-teal-600 hover:text-teal-700"
          }`}
        >
          All
        </button>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => handleCategoryChange(c)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium ${
              category === c ? "bg-teal-600 text-white" : "border border-slate-200 bg-white text-slate-600 hover:border-teal-600 hover:text-teal-700"
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search within results…"
            className="w-full rounded-full border border-slate-200 bg-white py-2 pl-10 pr-4 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
          />
        </form>

        <label className="ml-auto flex items-center gap-2 text-sm text-slate-600">
          Sort
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortOption)}
            className="rounded-full border border-slate-200 bg-white px-3 py-2 text-sm focus:border-teal-600 focus:outline-none"
          >
            <option value="relevance">Relevance</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
          </select>
        </label>
      </div>

      {error && <p className="text-red-600">Could not load products. Is the API running?</p>}

      {loading && offset === 0 && <ProductCardSkeletonGrid count={6} />}

      {!loading && !error && sortedProducts.length === 0 && (
        <EmptyState
          icon={PackageSearch}
          title="No products found"
          message="Try a different search term or browse another category."
          actionLabel="Browse all products"
          actionTo="/shop"
        />
      )}

      {sortedProducts.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sortedProducts.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      )}

      {canLoadMore && (
        <div className="flex justify-center">
          <button
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            disabled={loading}
            className="rounded-full border border-slate-200 bg-white px-5 py-2 text-sm font-medium text-slate-700 hover:border-teal-600 hover:text-teal-700 disabled:opacity-50"
          >
            {loading ? "Loading…" : "Load more"}
          </button>
        </div>
      )}
    </div>
  );
}
