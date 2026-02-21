import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");

  const onSubmit = (e) => {
    e.preventDefault();
    const result = login(form.username.trim(), form.password);
    if (result.success) {
      navigate("/");
      return;
    }
    setError(result.message || "Login failed");
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <h1>PhysioAssist AI</h1>
        <p className="muted">Sign in to continue</p>
        <form onSubmit={onSubmit} className="login-form">
          <label>
            Username
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
              placeholder="ziad_baher10"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
              placeholder="••••••••"
              required
            />
          </label>
          {error && <p className="error-text">{error}</p>}
          <button type="submit" className="primary-btn">Login</button>
        </form>
      </section>
    </main>
  );
}
