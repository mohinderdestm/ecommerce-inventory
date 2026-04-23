import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import "../index.css";

export default function Login() {
  const navigate = useNavigate();
  const [show, setShow] = useState(false);

  const [data, setData] = useState({
    email: "",
    password: ""
  });

  const handleLogin = async () => {
  try {
    await API.post("/login", data);

    const me = await API.get("/me"); 
    const role = me.data.role;

    if (role === "admin" || role === "inventory_manager") {
      navigate("/dashboard");
    } else {
      navigate("/products");
    }

  } catch {
    alert("Invalid credentials");
  }
};

  return (
    <div className="auth-page">
      <div className="auth-box">
        <h2>Welcome Back 👋</h2>

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

        <button className="primary" onClick={handleLogin}>
          Login
        </button>

        <p onClick={() => navigate("/signup")} className="link">
          Create Account
        </p>
      </div>
    </div>
  );
}