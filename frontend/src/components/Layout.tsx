import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Footer } from "./Footer";

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-canvas text-slate-900">
      <div className="bg-teal-700 px-4 py-2 text-center text-xs font-medium text-white">
        Free shipping on orders over $35 • OTC essentials — product info only, not medical advice
      </div>

      <Header />

      <main className="flex-1">
        <Outlet />
      </main>

      <Footer />
    </div>
  );
}
