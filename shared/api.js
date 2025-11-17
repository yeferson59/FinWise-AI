import axios from "axios";

const API_BASE_URL = "http://localhost:8000"; // <- reemplazar

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
  terms_and_conditions,
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
export const createTransaction = (tx) => api.post("/api/v1/transactions", tx);

// NLP solo texto
export const processText = (text, user_id, source_id = 1) =>
  api.post("/api/v1/transactions/process-text", {
    text,
    user_id,
    source_id,
  });

// NLP + OCR (archivo)
export const processFile = async (
  file,
  user_id,
  source_id = 1,
  document_type = "photo",
) => {
  // Convert file URI to Blob for RN FormData
  const response = await fetch(file.uri);
  const blob = await response.blob();

  const form = new FormData();
  form.append("file", blob, file.name);

  // Let axios set the Content-Type with boundary automatically
  return api.post(
    `/api/v1/transactions/process-from-file?user_id=${user_id}&source_id=${source_id}&document_type=${document_type}`,
    form,
  );
};

export default api;
