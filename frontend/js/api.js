const BASE_URL = "";

function getToken() {
  return localStorage.getItem("token");
}

async function apiRequest(endpoint, method = "GET", body = null) {
  const headers = {};

  if (body && !(body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();

  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }

  const config = {
    method,
    headers
  };

  if (body) {
    config.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  const response = await fetch(BASE_URL + endpoint, config);
  
  // Handle 401 - Unauthorized
  if (response.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/";
    throw new Error("Session expired");
  }

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "API Error");
  }

  return data;
}