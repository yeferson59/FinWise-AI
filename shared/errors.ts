/**
 * Error types and utilities for API responses
 */

export interface ApiErrorResponse {
  detail: string;
  error_code: string;
  status_code: number;
}

export interface ApiError extends Error {
  status?: number;
  error_code?: string;
  details?: any;
}

export enum ErrorType {
  NETWORK = "NETWORK_ERROR",
  INVALID_CREDENTIALS = "INVALID_CREDENTIALS",
  USER_NOT_FOUND = "USER_NOT_FOUND",
  PASSWORD_MISMATCH = "PASSWORD_MISMATCH",
  TERMS_NOT_ACCEPTED = "TERMS_NOT_ACCEPTED",
  EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS",
  VALIDATION = "VALIDATION_ERROR",
  SERVER = "SERVER_ERROR",
  UNKNOWN = "UNKNOWN_ERROR",
}

export const ERROR_MESSAGES: Record<string, string> = {
  INVALID_CREDENTIALS: "Email o contraseña incorrectos",
  USER_NOT_FOUND: "Usuario no encontrado",
  PASSWORD_MISMATCH: "Las contraseñas no coinciden",
  TERMS_NOT_ACCEPTED: "Debes aceptar los términos y condiciones",
  EMAIL_ALREADY_EXISTS: "Este email ya está registrado",
  NETWORK_ERROR: "Error de conexión. Intenta de nuevo.",
  SERVER_ERROR: "Error del servidor. Intenta de nuevo más tarde.",
  VALIDATION_ERROR: "Datos inválidos. Verifica los campos.",
  UNKNOWN_ERROR: "Algo salió mal. Intenta de nuevo.",
};

/**
 * Parse error response from API
 */
export const parseApiError = (error: any): ApiError => {
  const apiError: ApiError = new Error();

  if (error.response?.status) {
    apiError.status = error.response.status;
    apiError.message = error.response.data?.detail || "Error desconocido";
    apiError.error_code = error.response.data?.error_code || "UNKNOWN_ERROR";
    apiError.details = error.response.data;
  } else if (error.code) {
    apiError.error_code = error.code;
    apiError.message = ERROR_MESSAGES[error.code] || error.message;
  } else {
    apiError.error_code = "UNKNOWN_ERROR";
    apiError.message = error.message || ERROR_MESSAGES.UNKNOWN_ERROR;
  }

  return apiError;
};

/**
 * Check if error is retryable
 */
export const isRetryableError = (
  error: any,
  retryableStatuses: number[],
): boolean => {
  if (error.response?.status) {
    return retryableStatuses.includes(error.response.status);
  }

  const retryableCodes = [
    "ECONNREFUSED",
    "ECONNRESET",
    "ETIMEDOUT",
    "EHOSTUNREACH",
    "ENETUNREACH",
  ];

  return retryableCodes.includes(error.code);
};
