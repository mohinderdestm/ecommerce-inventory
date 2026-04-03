const BASE_URL = "http://127.0.0.1:8000/auth";

function setAuthBackground() {
  document.body.className = "auth-bg";
}

function setDashboardBackground() {
  document.body.className = "dashboard-bg";
}

// SWITCH UI
function showRegister() {
  loginBox.style.display = "none";
  registerBox.style.display = "block";
  setAuthBackground();
}

function showLogin() {
  registerBox.style.display = "none";
  loginBox.style.display = "block";
  setAuthBackground();
}

//validation
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isStrongPassword(password) {
  return password.length >= 6;
}

// REGISTER
async function register() {
  const data = {
    name: document.getElementById("name").value.trim(),
    email: document.getElementById("email").value.trim(),
    password: document.getElementById("password").value,
    role: document.getElementById("role").value,
  };

  // VALIDATION
  if (!data.name) {
    registerMsg.innerText = "Name is required";
    registerMsg.className = "error";
    return;
  }

  if (!isValidEmail(data.email)) {
    registerMsg.innerText = "Invalid email format";
    registerMsg.className = "error";
    return;
  }

  if (!isStrongPassword(data.password)) {
    registerMsg.innerText = "Password must be at least 6 characters";
    registerMsg.className = "error";
    return;
  }

  if (!data.role) {
    registerMsg.innerText = "Please select a role";
    registerMsg.className = "error";
    return;
  }

  const validRoles = ['admin', 'inventory_manager', 'warehouse_staff', 'finance_staff', 'viewer'];
if (!validRoles.includes(data.role)) {
  registerMsg.innerText = "Invalid role selected";
  registerMsg.className = "error";
  return;
}

  registerMsg.innerText = "Registering...";
  registerMsg.className = "";

  try {
    const res = await fetch(`${BASE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    const result = await res.json();
    console.log("REGISTER:", res.status, result);

    if (res.ok) {
      registerMsg.innerText = "Registration successful!";
      setTimeout(() => {
        localStorage.setItem("token", result.access_token);
        loadDashboard();
      }, 2000);
    } else {
      registerMsg.innerText =
        result.detail?.[0]?.msg || result.detail || "Registration failed";
    }
  } catch (err) {
    registerMsg.innerText = "Network error";
  }
}

// LOGIN
async function login() {
  const data = {
    email: loginEmail.value,
    password: loginPassword.value,
  };

       // VALIDATION
  if (!isValidEmail(data.email)) {
    loginMsg.innerText = "Enter valid email";
    loginMsg.className = "error";
    return;
  }

  if (!data.password) {
    loginMsg.innerText = "Password is required";
    loginMsg.className = "error";
    return;
  }

  loginMsg.innerText = "Logging in...";
  loginMsg.className = "";

  try {
  const res = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  const result = await res.json();

  if (res.ok) {
    localStorage.setItem("token", result.access_token);
    loadDashboard();
  } else {
    loginMsg.innerText = result.detail || "Login failed";
    loginMsg.className = "error";
  }

} catch (error) {
  loginMsg.innerText = "Server error. Try again later.";
  loginMsg.className = "error";
}}


// LOAD DASHBOARD
async function loadDashboard() {
  loginBox.style.display = "none";
  registerBox.style.display = "none";
  dashboard.style.display = "block";
  setDashboardBackground();

  const token = localStorage.getItem("token");

  const res = await fetch(`${BASE_URL}/me`, {
    headers: { Authorization: "Bearer " + token },
  });

  const data = await res.json();
  console.log("ME RESPONSE:", data);

  // nameTop.innerText = data.user.name;
  nameTop.innerText = data.user?.name || "User";
}

// NAVIGATION
function goTo(section) {
  if (section === "profile") {
    content.innerHTML = `<h3>Profile</h3><p>Name: ${nameTop.innerText}</p>`;
  }

  if (section === "products") {
    content.innerHTML = `<h3>Products</h3><p>Coming soon...</p>`;
  }

  if (section === "orders") {
    content.innerHTML = `<h3>Orders</h3><p>Coming soon...</p>`;
  }
}

// LOGOUT
function logout() {
  localStorage.removeItem("token");
  location.reload();
}

// AUTO LOGIN
if (localStorage.getItem("token")) {
  loadDashboard();
}
