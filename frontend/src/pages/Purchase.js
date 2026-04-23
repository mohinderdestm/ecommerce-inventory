import { useEffect, useState } from "react";
import API from "../api";
import Layout from "../components/Layout";
import "../styles/purchase.css";

export default function Purchase() {

  const [user, setUser] = useState(null);
  const [pos, setPos] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [suppliers, setSuppliers] = useState([]);

  const [form, setForm] = useState({
    warehouse_id: "",
    supplier_email: "",
    items: []
  });

  const [sku, setSku] = useState("");
  const [qty, setQty] = useState("");



  const load = async () => {

    try {

      const me = await API.get("/me");
      setUser(me.data);

      const poRes = await API.get("/purchase");
      const warehouseRes = await API.get("/warehouse");
      const productRes = await API.get("/products");

      setPos(poRes.data || []);
      setWarehouses(warehouseRes.data || []);

      let products = [];

      if (Array.isArray(productRes.data)) {
        products = productRes.data;
      }
      else if (Array.isArray(productRes.data.data)) {
        products = productRes.data.data;
      }

      const supplierEmails = products
        .map((p) => p.supplier_email)
        .filter((email) => email);

      setSuppliers([...new Set(supplierEmails)]);

    } catch (err) {
      console.log(err);
      alert("Error loading purchase data");
    }
  };

  useEffect(() => {
    load();
  }, []);




  const addItem = () => {

    if (!sku || !qty) {
      return alert("Enter SKU and Quantity");
    }

    setForm((prev) => ({
      ...prev,
      items: [
        ...prev.items,
        {
          sku,
          quantity: Number(qty)
        }
      ]
    }));

    setSku("");
    setQty("");
  };



  const removeItem = (index) => {

    const updated = [...form.items];

    updated.splice(index, 1);

    setForm({
      ...form,
      items: updated
    });
  };



  const createPO = async () => {

    if (!form.warehouse_id) {
      return alert("Select warehouse");
    }

    if (!form.supplier_email) {
      return alert("Select supplier");
    }

    if (form.items.length === 0) {
      return alert("Add at least one item");
    }

    try {

      await API.post("/purchase", form);


      setForm({
        warehouse_id: "",
        supplier_email: "",
        items: []
      });

      load();

    } catch (err) {

      console.log(err);

      alert(
        err.response?.data?.detail ||
        "Error creating purchase order"
      );
    }
  };


  const updateStatus = async (id, status) => {

    try {

      await API.put(`/purchase/status/${id}`, {
        status
      });

      alert(`PO marked as ${status}`);

      load();

    } catch (err) {

      console.log(err);

      alert(
        err.response?.data?.detail ||
        "Failed to update status"
      );
    }
  };


  const getStatusClass = (status) => {

    switch (status) {

      case "approved":
        return "status-approved";

      case "rejected":
        return "status-rejected";

      case "cancelled":
        return "status-cancelled";

      case "received":
        return "status-received";

      case "submitted":
        return "status-submitted";

      default:
        return "status-draft";
    }
  };


  return (

    <Layout user={user}>

      <div className="purchase-page">

        <div className="purchase-header">
          <div>
            <h1>Purchase Orders</h1>
          </div>
        </div>


    

        <div className="purchase-create-card">

          <div className="card-header">
            <h2>Create Purchase Order</h2>
          </div>


    

          <div className="form-group">

            <label>Select Warehouse</label>

            <select
              value={form.warehouse_id}
              onChange={(e) =>
                setForm({
                  ...form,
                  warehouse_id: e.target.value
                })
              }
            >

              <option value="">
                Choose Warehouse
              </option>

              {warehouses.map((w) => (
                <option
                  key={w._id}
                  value={w._id}
                >
                  {w.name}
                </option>
              ))}

            </select>

          </div>



          <div className="form-group">

            <label>Select Supplier</label>

            <select
              value={form.supplier_email}
              onChange={(e) =>
                setForm({
                  ...form,
                  supplier_email: e.target.value
                })
              }
            >

              <option value="">
                Choose Supplier
              </option>

              {suppliers.map((email, index) => (
                <option
                  key={index}
                  value={email}
                >
                  {email}
                </option>
              ))}

            </select>

          </div>



          <div className="item-input-row">

            <input
              type="text"
              placeholder="Enter Product SKU"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
            />

            <input
              type="number"
              placeholder="Quantity"
              value={qty}
              onChange={(e) => setQty(e.target.value)}
            />

            <button
              className="primary-btn"
              onClick={addItem}
            >
              Add Item
            </button>

          </div>


       
          <div className="purchase-items">

            {form.items.length === 0 ? (

              <div className="empty-items">
                No items added yet
              </div>

            ) : (

              form.items.map((item, index) => (

                <div
                  className="purchase-item-row"
                  key={index}
                >

                  <div>
                    <h4>{item.sku}</h4>
                    <p>Quantity: {item.quantity}</p>
                  </div>

                  <button
                    className="danger-btn"
                    onClick={() => removeItem(index)}
                  >
                    Remove
                  </button>

                </div>

              ))
            )}

          </div>



          <button
            className="create-btn"
            onClick={createPO}
          >
            Create Purchase Order
          </button>

        </div>



        <div className="purchase-orders-section">

          <div className="section-header">
            <h2>All Purchase Orders</h2>
          </div>

          <div className="purchase-grid">

            {pos.map((po) => {

              const warehouse = warehouses.find(
                (w) => w._id === po.warehouse_id
              );

              return (

                <div
                  className="purchase-card"
                  key={po._id}
                >

                  <div className="purchase-top">

                    <div>

                      <h3>
                        {warehouse?.name || "Warehouse"}
                      </h3>

                      <p>
                        Supplier: {po.supplier_email}
                      </p>

                      <p className="purchase-date">
                        {
                          new Date(
                            po.created_at
                          ).toLocaleDateString()
                        }
                      </p>

                    </div>

                    <span
                      className={getStatusClass(po.status)}
                    >
                      {po.status}
                    </span>

                  </div>


        

                  <div className="purchase-products">

                    {po.items.map((item, idx) => (

                      <div
                        className="purchase-product"
                        key={idx}
                      >

                        <div>
                          <strong>{item.sku}</strong>
                        </div>

                        <span>
                          Qty: {item.quantity}
                        </span>

                      </div>

                    ))}

                  </div>


            

                  <div className="po-actions">

                    {po.status === "draft" && (
                      <button
                        className="submit-btn"
                        onClick={() =>
                          updateStatus(
                            po._id,
                            "submitted"
                          )
                        }
                      >
                        Submit
                      </button>
                    )}


                    {po.status === "submitted" && (
                      <>

                        <button
                          className="approve-btn"
                          onClick={() =>
                            updateStatus(
                              po._id,
                              "approved"
                            )
                          }
                        >
                          Approve
                        </button>

                        <button
                          className="reject-btn"
                          onClick={() =>
                            updateStatus(
                              po._id,
                              "rejected"
                            )
                          }
                        >
                          Reject
                        </button>

                      </>
                    )}


                    {po.status === "approved" && (
                      <>

                        <button
                          className="receive-btn"
                          onClick={() =>
                            updateStatus(
                              po._id,
                              "received"
                            )
                          }
                        >
                          Mark Received
                        </button>

                        <button
                          className="cancel-btn"
                          onClick={() =>
                            updateStatus(
                              po._id,
                              "cancelled"
                            )
                          }
                        >
                          Cancel
                        </button>

                      </>
                    )}

                  </div>

                </div>

              );
            })}

          </div>

        </div>

      </div>

    </Layout>
  );
}
