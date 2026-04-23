import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";

export default function AdminCart() {

  const [carts, setCarts] = useState([]);
  const [user, setUser] = useState(null);

  const load = async () => {
    try {
      const me = await API.get("/me");
      setUser(me.data);

      const res = await API.get("/cart/all");
      setCarts(res.data);

    } catch (err) {
      console.log(err);
      window.location = "/";
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <Layout user={user}>
      <h2>All User Carts</h2>

      <div className="grid">
        {carts.map(cart => (
          <div className="card" key={cart._id}>

            <h3>User: {cart.user_id}</h3>

            {/* ✅ ITEMS LOOP */}
            {cart.items?.length > 0 ? (
              cart.items.map((item, i) => (
                <div key={i} className="inventory-item">
                  <p>SKU: {item.variant_sku}</p>
                  <p>Qty: {item.quantity}</p>
                </div>
              ))
            ) : (
              <p>No items</p>
            )}


          </div>
        ))}
      </div>
    </Layout>
  );
}