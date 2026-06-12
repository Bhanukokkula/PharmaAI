import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ChevronDown, LogOut, Pill, Search, ShoppingCart, User as UserIcon } from "lucide-react";
import { useCart } from "../lib/CartContext";
import { useAuth } from "../lib/AuthContext";
import { CATEGORIES } from "../lib/categories";

function AccountMenu() {
  const { user, isSignedIn, signOut } = useAuth();
  const [open, setOpen] = useState(false);

  if (!isSignedIn || !user) {
    return (
      <Link
        to="/login"
        className="flex items-center gap-1.5 rounded-full border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 hover:border-teal-600 hover:text-teal-700"
      >
        <UserIcon className="h-4 w-4" />
        Sign in
      </Link>
    );
  }

  const initial = user.display_name.trim().charAt(0).toUpperCase();

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-full border border-slate-200 px-2 py-1.5 pr-3 text-sm font-medium text-slate-700 hover:border-teal-600"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-teal-100 text-xs font-semibold text-teal-700">
          {initial}
        </span>
        <span className="hidden sm:inline">{user.display_name}</span>
        <ChevronDown className="h-4 w-4 text-slate-400" />
      </button>

      {open && (
        <>
          <button
            aria-label="Close menu"
            className="fixed inset-0 z-10 cursor-default"
            onClick={() => setOpen(false)}
          />
          <div
            role="menu"
            className="absolute right-0 z-20 mt-2 w-44 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
          >
            <Link
              to="/account"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-slate-700 hover:bg-teal-50 hover:text-teal-700"
            >
              Account
            </Link>
            <button
              role="menuitem"
              onClick={() => {
                setOpen(false);
                void signOut();
              }}
              className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-slate-700 hover:bg-teal-50 hover:text-teal-700"
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export function Header() {
  const { itemCount } = useCart();
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("q") ?? "");
  const navigate = useNavigate();

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    const trimmed = search.trim();
    navigate(trimmed ? `/shop?q=${encodeURIComponent(trimmed)}` : "/shop");
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 sm:gap-4">
        <Link to="/" className="flex shrink-0 items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600 text-white">
            <Pill className="h-5 w-5" />
          </span>
          <span className="hidden font-display text-xl font-bold text-slate-900 sm:inline">PharmaAI</span>
        </Link>

        <form onSubmit={handleSearch} className="relative min-w-0 flex-1 max-w-xl">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search pain relief, allergy, vitamins…"
            aria-label="Search products"
            className="w-full rounded-full border border-slate-200 bg-slate-50 py-2 pl-10 pr-4 text-sm text-slate-700 placeholder:text-slate-400 focus:border-teal-600 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-100"
          />
        </form>

        <nav className="ml-auto flex items-center gap-2 sm:gap-3">
          <Link
            to="/cart"
            aria-label="Cart"
            className="relative flex h-9 w-9 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100 hover:text-teal-700"
          >
            <ShoppingCart className="h-5 w-5" />
            {itemCount > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-teal-600 px-1 text-[11px] font-semibold text-white">
                {itemCount}
              </span>
            )}
          </Link>
          <AccountMenu />
        </nav>
      </div>

      <div className="border-t border-slate-100">
        <div className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-4 py-2 text-sm">
          {CATEGORIES.map((c) => (
            <Link
              key={c}
              to={`/shop?category=${encodeURIComponent(c)}`}
              className="shrink-0 rounded-full px-3 py-1 text-slate-600 hover:bg-teal-50 hover:text-teal-700"
            >
              {c}
            </Link>
          ))}
        </div>
      </div>
    </header>
  );
}
