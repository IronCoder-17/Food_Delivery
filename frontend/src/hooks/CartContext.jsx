import { createContext, useContext, useState, useCallback } from "react";
import { getCart } from "../services/endpoints";
import { useAuth } from "./AuthContext";

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const { role } = useAuth();
  const [cart, setCart] = useState({ items: [], subtotal: 0, delivery_fee: 0, total: 0 });

  const refreshCart = useCallback(async () => {
    if (role !== "customer") return;
    try {
      const res = await getCart();
      setCart(res.data);
    } catch (e) {
      // silently ignore; cart badge just won't update
    }
  }, [role]);

  const itemCount = cart.items.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <CartContext.Provider value={{ cart, setCart, refreshCart, itemCount }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error("useCart must be used within CartProvider");
  return ctx;
}
