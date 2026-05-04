import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import "../styles/signup.css";

export default function Signup() {
  const navigate = useNavigate();
  const [show, setShow] = useState(false);

  const [data, setData] = useState({
    name: "",
    email: "",
    password: "",
    role: ""
  });

  const handleSignup = async () => {
    try {
      await API.post("/signup", data);
      navigate("/");
    } catch {
      alert("Signup failed");
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h2>Create Account 🚀</h2>

        <input placeholder="Name" onChange={e => setData({...data, name: e.target.value})} />
        <input placeholder="Email" onChange={e => setData({...data, email: e.target.value})} />

        <div className="password-box">
          <input
            type={show ? "text" : "password"}
            placeholder="Password"
            onChange={e => setData({...data, password: e.target.value})}
          />
          <span onClick={() => setShow(!show)}>
            {show ? "🙈" : "👁"}
          </span>
        </div>

        <select onChange={e => setData({...data, role: e.target.value})}>
          <option value="viewer">Viewer</option>
          <option value="admin">Admin</option>
          <option value="supplier">Supplier</option>
          <option value="inventory_manager">Inventory Manager</option>
          <option value="warehouse_staff">Warehouse Staff</option>
        </select>

        <button className="primary" onClick={handleSignup}>
          Signup
        </button>

        <p className="link" onClick={() => navigate("/")}>
          Already have an account?
        </p>
      </div>
    </div>
  );
}