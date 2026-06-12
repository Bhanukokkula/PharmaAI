import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type Cart } from "./api";

interface CartContextValue {
  cart: Cart;
  itemCount: number;
  loading: boolean;
  refresh: () => Promise<void>;
  addToCart: (productId: number, quantity?: number) => Promise<void>;
  updateItem: (itemId: number, quantity: number) => Promise<void>;
  removeItem: (itemId: number) => Promise<void>;
}

const EMPTY_CART: Cart = { items: [], total: 0 };

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<Cart>(EMPTY_CART);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setCart(await api.getCart());
    } catch {
      setCart(EMPTY_CART);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const addToCart = useCallback(async (productId: number, quantity = 1) => {
    setCart(await api.addToCart(productId, quantity));
  }, []);

  const updateItem = useCallback(async (itemId: number, quantity: number) => {
    setCart(await api.updateCartItem(itemId, quantity));
  }, []);

  const removeItem = useCallback(async (itemId: number) => {
    setCart(await api.removeCartItem(itemId));
  }, []);

  const itemCount = cart.items.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <CartContext.Provider value={{ cart, itemCount, loading, refresh, addToCart, updateItem, removeItem }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within a CartProvider");
  return ctx;
}
