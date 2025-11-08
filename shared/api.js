import axios from "axios";

const API_BASE_URL = "http://192.168.128.13:8000/"; // <- reemplazar

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" }
});

export const login = (email, password) =>
  api.post("/api/v1/auth/login", { email, password });

export default api;
