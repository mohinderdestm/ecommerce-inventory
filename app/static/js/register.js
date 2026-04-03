const form = document.getElementById("registerForm");
const errorMsg = document.getElementById("errorMsg");
const successMsg = document.getElementById("successMsg");

function goBack() {
  window.location.href = "/";
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

  const name = document.getElementById("name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const role = document.getElementById("role").value;

  if (!name || !email || !password) {
    showError("All fields are required");
    return;
  }

  if (password.length < 6) {
    showError("Password must be at least 6 characters");
    return;
  }

  try {
    const res = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name, email, password, role }),
    });

    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || "Registration failed");
      return;
    }

    showSuccess("Registration successful");

    setTimeout(() => {
      window.location.href = "/";
    }, 1500);
  } catch (err) {
    showError("Server error. Please try again");
  }
});
