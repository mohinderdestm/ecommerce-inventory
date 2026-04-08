document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("supplierForm");
  const errorMsg = document.getElementById("errorMsg");
  const successMsg = document.getElementById("successMsg");

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const payload = {
        name: document.getElementById("name").value.trim(),
        contact_person: document.getElementById("contact_person").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value.trim(),
        phone: document.getElementById("phone").value.trim(),
        address: document.getElementById("address").value.trim(),
        gst: document.getElementById("gst").value.trim(),
        payment_terms: document.getElementById("payment_terms").value.trim(),
        role: "supplier",
      };

      if (payload.password.length < 6) {
        showError("Password must be at least 6 characters");
        return;
      }

      try {
        const btn = document.getElementById("submitBtn");
        btn.innerText = "Processing...";
        btn.disabled = true;

        const res = await fetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
          showError(data.detail || "Registration failed");
          btn.innerText = "Register Business";
          btn.disabled = false;
          return;
        }

        showSuccess("Business registered successfully!");
        setTimeout(() => {
          window.location.href = "/";
        }, 2000);
      } catch (err) {
        showError("Connection error. Please try again.");
        document.getElementById("submitBtn").disabled = false;
        document.getElementById("submitBtn").innerText = "Register Business";
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
