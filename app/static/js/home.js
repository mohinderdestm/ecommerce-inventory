const token = localStorage.getItem("access_token");

if (!token) {
  window.location.href = "/";
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.clear();
  window.location.href = "/";
});
