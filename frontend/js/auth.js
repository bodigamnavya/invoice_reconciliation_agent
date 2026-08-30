/**
 * RECON AI - AUTHENTICATION MODULE (auth.js)
 */

const Auth = {
  TOKEN_KEY: "recon_jwt_token",
  USER_KEY: "recon_user_profile",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.location.href = "login.html";
  },

  requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = "login.html";
    } else {
      this.renderUserSnippet();
    }
  },

  checkAuthRedirect() {
    if (this.isAuthenticated()) {
      window.location.href = "dashboard.html";
    }
  },

  renderUserSnippet() {
    const user = this.getUser();
    if (!user) return;
    
    const nameEls = document.querySelectorAll(".user-name");
    const roleEls = document.querySelectorAll(".user-role");
    const avatarEls = document.querySelectorAll(".user-avatar");

    nameEls.forEach(el => el.textContent = user.full_name || "Finance Officer");
    roleEls.forEach(el => el.textContent = user.role || "Finance Analyst");
    avatarEls.forEach(el => {
      const initials = (user.full_name || "F").split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
      el.textContent = initials;
    });
  },

  async login(email, password) {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Invalid credentials.");

      this.setToken(data.token);
      this.setUser(data.user);
      return data;
    } catch (err) {
      throw err;
    }
  },

  async register(full_name, email, password, role = "Finance Analyst") {
    try {
      const res = await fetch(`${CONFIG.API_BASE}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ full_name, email, password, role })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Registration failed.");

      this.setToken(data.token);
      this.setUser(data.user);
      return data;
    } catch (err) {
      throw err;
    }
  }
};

// Global quick fill helper for demo
function fillDemoCredentials(email, pwd) {
  const emailInput = document.getElementById("email");
  const pwdInput = document.getElementById("password");
  if (emailInput && pwdInput) {
    emailInput.value = email;
    pwdInput.value = pwd;
    showToast("Filled demo controller credentials!", "info");
  }
}
