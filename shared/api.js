import axios from "axios";

const API_BASE_URL = "http://192.168.128.3:8081"; // <- reemplazar

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    Accept: "application/json",
  },
});

//LOGIN
export const login = (email, password) =>
  api.post("/api/v1/auth/login", { email, password });

//REGISTER
export const register = (
  first_name,
  last_name,
  email,
  password,
  confirm_password,
  terms_and_conditions
) =>
  api.post("/api/v1/auth/register", {
    first_name,
    last_name,
    email,
    password,
    confirm_password,
    terms_and_conditions,
  });

  //Transaccioones
  export const createTransaction = (tx) =>
  api.post("/api/v1/transactions", tx);

  // NLP solo texto
export const processText = (text, user_id, source_id = 1) =>
  api.post("/api/v1/transactions/process-text", {
    text,
    user_id,
    source_id
  });

// NLP + OCR (archivo)
export const processFile = (file, user_id, source_id = 1) => {
  const form = new FormData();
  form.append("file", file);

  return api.post(
    `/api/v1/transactions/process-from-file?user_id=${user_id}&source_id=${source_id}`,
    form,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );
};





export default api;
