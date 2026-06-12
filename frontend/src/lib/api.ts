const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

// In-memory only — this is a mock session (see AuthContext), not real auth.
// No localStorage/sessionStorage: signing out simply forgets this value and
// the API falls back to its default seeded user.
let activeUserId: number | null = null;

export function getActiveUserId(): number | null {
  return activeUserId;
}

export function setActiveUserId(userId: number | null) {
  activeUserId = userId;
}

export interface Product {
  id: number;
  brand_name: string;
  generic_name: string | null;
  category: string;
  purpose: string | null;
  active_ingredient: string | null;
  warnings: string | null;
  dosage_and_administration: string | null;
  route: string | null;
  product_ndc: string | null;
  rxcui: string | null;
  price: number;
}

export interface ProductList {
  total: number;
  items: Product[];
}

export interface User {
  id: number;
  username: string;
  display_name: string;
}

export interface Persona {
  id: number;
  display_name: string;
  segment_label: string;
}

export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
}

export interface Cart {
  items: CartItem[];
  total: number;
}

export interface OrderItem {
  product_id: number;
  product: Product;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: number;
  total: number;
  created_at: string;
  items: OrderItem[];
}

export interface RecommendationItem {
  product: Product;
  score: number;
  reason: string;
}

export interface RecommendationResponse {
  user_id: number;
  model_version: string;
  items: RecommendationItem[];
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const userId = getActiveUserId();
  if (userId !== null) {
    headers.set("X-User-Id", String(userId));
  }
  if (options.body) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  listCategories: () => request<string[]>("/catalog/categories"),
  listProducts: (params: { category?: string; q?: string; limit?: number; offset?: number } = {}) => {
    const search = new URLSearchParams();
    if (params.category) search.set("category", params.category);
    if (params.q) search.set("q", params.q);
    if (params.limit) search.set("limit", String(params.limit));
    if (params.offset) search.set("offset", String(params.offset));
    return request<ProductList>(`/catalog/products?${search.toString()}`);
  },
  getProduct: (id: number) => request<Product>(`/catalog/products/${id}`),
  listUsers: () => request<User[]>("/users"),
  listPersonas: () => request<Persona[]>("/users/personas"),
  getActiveUser: () => request<User>("/users/me"),
  getCart: () => request<Cart>("/cart"),
  addToCart: (productId: number, quantity = 1) =>
    request<Cart>("/cart/items", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, quantity }),
    }),
  updateCartItem: (itemId: number, quantity: number) =>
    request<Cart>(`/cart/items/${itemId}`, {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),
  removeCartItem: (itemId: number) =>
    request<Cart>(`/cart/items/${itemId}`, { method: "DELETE" }),
  checkout: () => request<Order>("/cart/checkout", { method: "POST" }),
  listOrders: () => request<Order[]>("/orders"),
  getRecommendations: (k = 10) =>
    request<RecommendationResponse>(`/recommend?k=${k}`),
};
