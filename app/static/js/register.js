document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("registerForm");
  const roleSelect = document.getElementById("role");
  const errorMsg = document.getElementById("errorMsg");
  const successMsg = document.getElementById("successMsg");

  if (roleSelect) {
    roleSelect.addEventListener("change", (e) => {
      if (e.target.value === "supplier") {
        console.log("Supplier selected, redirecting...");
        window.location.href = "/register-supplier";
      }
    });
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const name = document.getElementById("name").value.trim();
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value.trim();
      const role = roleSelect.value;

      if (!name || !email || !password) {
        showError("All fields are required");
        return;
      }

      try {
        const res = await fetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, email, password, role }),
        });

        const data = await res.json();

        if (!res.ok) {
          showError(data.detail || "Registration failed");
          return;
        }

        showSuccess("Registration successful!");
        setTimeout(() => {
          window.location.href = "/";
        }, 1500);
      } catch (err) {
        showError("Server error. Please try again");
      }
    });
  }

  function showError(message) {
    successMsg.innerText = "";
    errorMsg.innerText = message;
    errorMsg.classList.remove("show-error", "fade-out");
    void errorMsg.offsetWidth;
    errorMsg.classList.add("show-error");
  }

  function showSuccess(message) {
    errorMsg.innerText = "";
    successMsg.innerText = message;
    successMsg.classList.remove("show-success", "fade-out");
    void successMsg.offsetWidth;
    successMsg.classList.add("show-success");
  }
});

function goBack() {
  window.location.href = "/";
}
