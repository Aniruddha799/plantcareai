const API_BASE = "";

// Auth Token Management
function saveToken(token) {
    localStorage.setItem("access_token", token);
}

function getToken() {
    return localStorage.getItem("access_token");
}

function removeToken() {
    localStorage.removeItem("access_token");
}

function isAuthenticated() {
    return !!getToken();
}

function checkAuth() {
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath.endsWith("login.html") || currentPath.endsWith("register.html") || currentPath === "/frontend/" || currentPath === "/frontend";
    
    if (!isAuthenticated() && !isAuthPage) {
        window.location.href = "login.html";
    }
}

function checkRedirectAuth() {
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath.endsWith("login.html") || currentPath.endsWith("register.html");
    if (isAuthenticated() && isAuthPage) {
        window.location.href = "dashboard.html";
    }
}

// API Fetch Helper with Authorization headers
async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = options.headers || {};
    
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    
    // Auto format JSON requests unless it's FormData (for file uploads)
    if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
        headers["Content-Type"] = "application/json";
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });
    
    if (response.status === 401) {
        removeToken();
        window.location.href = "login.html";
        throw new Error("Session expired. Please log in again.");
    }
    
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "An error occurred");
    }
    return data;
}

// Dynamically Render Navbar across views
function renderNavbar() {
    const navbarContainer = document.getElementById("navbar-container");
    if (!navbarContainer) return;
    
    const currentPath = window.location.pathname;
    const isPage = (name) => currentPath.endsWith(name);
    
    const navbarHtml = `
        <nav class="navbar navbar-expand-lg navbar-dark navbar-custom py-3">
            <div class="container">
                <a class="navbar-brand d-flex align-items-center" href="dashboard.html">
                    <span class="fs-4 me-2">🌱</span><strong>PlantCare AI</strong>
                </a>
                <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                        <li class="nav-item">
                            <a class="nav-link ${isPage("dashboard.html") ? "active" : ""}" href="dashboard.html">Dashboard</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${isPage("plants.html") ? "active" : ""}" href="plants.html">My Plants</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${isPage("upload.html") ? "active" : ""}" href="upload.html">Scan Leaf</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link ${isPage("history.html") ? "active" : ""}" href="history.html">Scan History</a>
                        </li>
                    </ul>
                    <div class="d-flex align-items-center">
                        <button class="btn btn-outline-danger btn-sm border-0" id="logout-btn">Log Out</button>
                    </div>
                </div>
            </div>
        </nav>
    `;
    navbarContainer.innerHTML = navbarHtml;
    
    document.getElementById("logout-btn")?.addEventListener("click", () => {
        removeToken();
        window.location.href = "login.html";
    });
}

// UI Alert display helper
function showAlert(message, type = "danger", containerId = "alert-container") {
    const alertContainer = document.getElementById(containerId);
    if (!alertContainer) return;
    
    alertContainer.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show border-0 shadow-sm glass-card text-light" role="alert" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);">
            <div class="d-flex align-items-center">
                <span class="me-2 fs-5">${type === "success" ? "✓" : "⚠"}</span>
                <div>${message}</div>
            </div>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        </div>
    `;
}

// Auto run Auth Checks
checkAuth();
document.addEventListener("DOMContentLoaded", () => {
    renderNavbar();
});
