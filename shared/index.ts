import axios, { type AxiosInstance } from "axios";
import CONFIG from "./config";
import { parseApiError, isRetryableError, type ApiError } from "./errors";
import { z } from "zod";

const UserSchema = z.object({
  access_token: z.string(),
  user: z.object({
    id: z.coerce.number(),
    email: z.email(),
    first_name: z.coerce.string(),
    last_name: z.coerce.string(),
  }),
  success: z.boolean(),
});

const RegisterResponseSchema = z.object({
  message: z.string(),
  success: z.boolean(),
});

/**
 * Create axios instance with retry interceptor
 */
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: CONFIG.API_BASE_URL,
    timeout: CONFIG.API_TIMEOUT,
    headers: {
      Accept: "application/json",
    },
  });

  // Add response interceptor for error handling
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      const parsedError = parseApiError(error);
      return Promise.reject(parsedError);
    },
  );

  return instance;
};

const api = createApiInstance();

/**
 * Retry logic with exponential backoff
 */
const withRetry = async <T>(
  fn: () => Promise<T>,
  maxAttempts: number = CONFIG.RETRY.MAX_ATTEMPTS,
): Promise<T> => {
  let lastError: any;
  let delay = CONFIG.RETRY.INITIAL_DELAY;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx) except specific codes
      const status = (error as any)?.status;
      if (status && status >= 400 && status < 500) {
        // Don't retry 4xx errors except 408 and 429
        if (status !== 408 && status !== 429) {
          throw error;
        }
      }

      // Check if error is retryable
      if (!isRetryableError(error, CONFIG.RETRYABLE_STATUS_CODES)) {
        throw error;
      }

      // Don't retry on last attempt
      if (attempt === maxAttempts) {
        throw error;
      }

      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, delay));

      // Increase delay for next attempt (exponential backoff)
      delay = Math.min(
        delay * CONFIG.RETRY.BACKOFF_MULTIPLIER,
        CONFIG.RETRY.MAX_DELAY,
      );

      console.log(
        `Retry attempt ${attempt + 1}/${maxAttempts} after ${delay}ms`,
      );
    }
  }

  throw lastError;
};

// ============================================================================
// AUTH ENDPOINTS
// ============================================================================

/**
 * Login with email and password
 */
export const login = async (
  email: string,
  password: string,
): Promise<z.infer<typeof UserSchema> | null> => {
  try {
    return await withRetry(async () => {
      const response = await api.post("/api/v1/auth/login", {
        email,
        password,
      });

      const { success, data } = await UserSchema.safeParseAsync(response.data);

      if (!success) {
        const error = new Error("Invalid response format") as ApiError;
        error.error_code = "VALIDATION_ERROR";
        error.status = 500;
        throw error;
      }

      return data;
    });
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Login Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return null;
  }
};

/**
 * Register new user
 */
export const register = async (
  first_name: string,
  last_name: string,
  email: string,
  password: string,
  confirm_password: string,
  terms_and_conditions: boolean,
): Promise<z.infer<typeof RegisterResponseSchema> | null> => {
  try {
    return await withRetry(async () => {
      const response = await api.post("/api/v1/auth/register", {
        first_name,
        last_name,
        email,
        password,
        confirm_password,
        terms_and_conditions,
      });

      const { success, data } = await RegisterResponseSchema.safeParseAsync(
        response.data,
      );

      if (!success) {
        const error = new Error("Invalid response format") as ApiError;
        error.error_code = "VALIDATION_ERROR";
        error.status = 500;
        throw error;
      }

      return data;
    });
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Register Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return null;
  }
};

/**
 * Logout and invalidate session
 */
export const logout = async (): Promise<boolean> => {
  try {
    await withRetry(async () => {
      await api.post("/api/v1/auth/logout");
    });
    return true;
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Logout Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return false;
  }
};

// ============================================================================
// TRANSACTIONS
// ============================================================================

export const createTransaction = async (tx: any) =>
  api.post("/api/v1/transactions", tx);

// NLP solo texto
export const processText = async (
  text: string,
  user_id: number,
  source_id: number = 1,
) =>
  api.post("/api/v1/transactions/process-text", {
    text,
    user_id,
    source_id,
  });

// NLP + OCR (archivo)
export const processFile = async (
  file: { uri: string; name: string },
  user_id: number,
  source_id = 1,
  document_type = "photo",
) => {
  const form = new FormData();
  form.append("file", {
    uri: file.uri,
    name: file.name,
    type: "image/jpeg",
  } as any);

  return api.post(
    `/api/v1/transactions/process-from-file?user_id=${user_id}&source_id=${source_id}&document_type=${document_type}`,
    form,
  );
};

export default api;
