import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";

export default function Cart() {

  const [cart, setCart] = useState([]);
  const [total, setTotal] = useState(0);
  const [user, setUser] = useState(null);

  const load = async () => {

    try {

      const me = await API.get("/me");
      setUser(me.data);

      const res = await API.get("/cart");

      setCart(res.data.items || []);
      setTotal(res.data.total || 0);

    } catch (err) {

      console.log(err);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const updateQuantity = async (
    variantId,
    quantity
  ) => {

    try {

      await API.put(
        "/cart/update",
        {
          variant_id: variantId,
          quantity
        }
      );

      load();

    } catch (err) {

      alert(
        err.response?.data?.detail || "Error"
      );
    }
  };

  const checkout = async () => {

    try {

      await API.post("/cart/checkout");

      alert("Order placed");

      load();

    } catch (err) {

      alert(
        err.response?.data?.detail || "Error"
      );
    }
  };

  return (

    <Layout user={user}>

      <div className="page">

        <h2>My Cart</h2>

        <div className="grid">

          {cart.map((item, i) => (

            <div key={i} className="card">

              <img
                src={
                  item.image
                    ? `http://localhost:8000/${item.image}`
                    : "https://via.placeholder.com/150"
                }
                alt=""
              />

              <h3>{item.name}</h3>

              <p>
                {item.color} / {item.size}
              </p>

              <p>
                SKU: {item.sku}
              </p>

              <p>
                ₹{item.price}
              </p>

              <div
                style={{
                  display: "flex",
                  gap: "10px",
                  alignItems: "center",
                  marginTop: "10px"
                }}
              >

                <button
                  onClick={() =>
                    updateQuantity(
                      item.variant_id,
                      item.quantity - 1
                    )
                  }
                >
                  -
                </button>

                <b>
                  {item.quantity}
                </b>

                <button
                  onClick={() =>
                    updateQuantity(
                      item.variant_id,
                      item.quantity + 1
                    )
                  }
                >
                  +
                </button>

              </div>

              <p
                style={{
                  marginTop: "10px"
                }}
              >
                Subtotal:
                {" "}
                ₹{item.subtotal}
              </p>

            </div>
          ))}

        </div>

        <h2>
          Total: ₹{total}
        </h2>

        {cart.length > 0 && (

          <button onClick={checkout}>
            Place Order
          </button>

        )}

      </div>

    </Layout>
  );
}

