let isLogin = true;

const form = document.getElementById("authForm");
const message = document.getElementById("message");

// auto redirect if already logged in
(function checkAuth() {
  const token = localStorage.getItem("token");
  if (token) {
    window.location.href = "/dashboard";
  }
})();

function toggleMode() {
  isLogin = !isLogin;

  document.getElementById("title").innerText = isLogin ? "Login" : "Sign Up";

  document.getElementById("name").style.display = isLogin ? "none" : "block";
  document.getElementById("role").style.display = isLogin ? "none" : "block";

  document.getElementById("toggleText").innerHTML = isLogin
    ? `Don't have an account? <span onclick="toggleMode()">Sign Up</span>`
    : `Already have an account? <span onclick="toggleMode()">Login</span>`;
  
  // Clear message when toggling
  message.innerText = "";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  // Basic validation
  if (!email || !password) {
    message.innerText = "Please fill all fields";
    message.style.color = "red";
    return;
  }

  try {
    let response;

    if (isLogin) {
      // LOGIN
      response = await fetch("/auth/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email, password })
      });

    } else {
      // SIGNUP
      const name = document.getElementById("name").value.trim();
      const role = document.getElementById("role").value;

      if (!name) {
        message.innerText = "Please enter your name";
        message.style.color = "red";
        return;
      }

      response = await fetch("/auth/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ name, email, password, role })
      });
    }

    const data = await response.json();

    if (!response.ok) {
      message.innerText = data.detail || "An error occurred";
      message.style.color = "red";
      return;
    }

    // if login → save token
    if (isLogin) {
      localStorage.setItem("token", data.access_token);
      window.location.href = "/dashboard";
    } else {
      message.innerText = "Signup successful! Please login.";
      message.style.color = "green";
      form.reset();
      toggleMode();
    }

  } catch (err) {
    console.error(err);
    message.innerText = "Server error. Please try again.";
    message.style.color = "red";
  }
});