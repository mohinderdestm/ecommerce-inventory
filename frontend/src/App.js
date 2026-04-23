import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Products from "./pages/Products";
import Variants from "./pages/Variants";
import Orders from "./pages/orders";
import Warehouses from "./pages/Warehouses";
import Cart from "./pages/Cart";
import AdminCart from "./pages/AdminCart";
import Purchase from "./pages/Purchase";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/products" element={<Products />} />
        <Route path="/variants/:id" element={<Variants />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/warehouses" element={<Warehouses />} />
        <Route path="/cart" element={<Cart />} />
        <Route path="/admin-carts" element={<AdminCart />} />
        <Route path="/purchase" element={<Purchase />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;