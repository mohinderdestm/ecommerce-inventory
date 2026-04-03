const form = document.getElementById("loginForm");
const errorMsg = document.getElementById("errorMsg");
const successMsg = document.getElementById("successMsg");

const token = localStorage.getItem("access_token");
if (token && window.location.pathname === "/") {
  window.location.href = "/home";
}

function showError(message) {
  successMsg.innerText = "";
  errorMsg.innerText = message;

  errorMsg.classList.remove("show-error", "fade-out");
  void errorMsg.offsetWidth;
  errorMsg.classList.add("show-error");

  setTimeout(() => {
    errorMsg.classList.add("fade-out");
    setTimeout(() => {
      errorMsg.innerText = "";
      errorMsg.classList.remove("show-error", "fade-out");
    }, 300);
  }, 3000);
}

function showSuccess(message) {
  errorMsg.innerText = "";
  successMsg.innerText = message;

  successMsg.classList.remove("show-success", "fade-out");
  void successMsg.offsetWidth;
  successMsg.classList.add("show-success");

  setTimeout(() => {
    successMsg.classList.add("fade-out");
    setTimeout(() => {
      successMsg.innerText = "";
      successMsg.classList.remove("show-success", "fade-out");
    }, 300);
  }, 2000);
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!email || !password) {
    showError("All fields are required");
    return;
  }

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || "Invalid email or password");
      return;
    }

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("user_role", data.role);
    localStorage.setItem("user_email", data.email);

    showSuccess("Login successful");

    setTimeout(() => {
      window.location.href = "/home";
    }, 1200);
  } catch (err) {
    showError("Server error. Please try again");
  }
});
