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

const TransactionSchema = z.object({
  id: z.coerce.string(),
  user_id: z.coerce.number(),
  category_id: z.coerce.number(),
  source_id: z.coerce.number(),
  title: z.coerce.string().optional().default(""),
  description: z.coerce.string(),
  amount: z.coerce.number(),
  transaction_type: z.enum(["income", "expense"]).default("expense"),
  date: z.string(),
  state: z.coerce.string(),
  updated_at: z.string(),
  created_at: z.string(),
});

const CreateTransaction = TransactionSchema.omit({
  id: true,
  state: true,
  created_at: true,
  updated_at: true,
});

const TransactionsSchema = z.array(TransactionSchema);

const CategorySchema = z.object({
  id: z.coerce.number(),
  name: z.coerce.string(),
  description: z.coerce.string().nullable().optional(),
  is_default: z.coerce.boolean(),
  user_id: z.coerce.number().nullable().optional(),
  updated_at: z.string(),
  created_at: z.string(),
});

const CategoriesSchema = z.array(CategorySchema);

const SourceSchema = z.object({
  id: z.coerce.number(),
  name: z.coerce.string(),
  description: z.coerce.string().nullable().optional(),
  is_default: z.coerce.boolean(),
  user_id: z.coerce.number().nullable().optional(),
  updated_at: z.string(),
  created_at: z.string(),
});

const SourcesSchema = z.array(SourceSchema);

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
 * Set the authorization token for API requests
 */
export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common["Authorization"];
  }
};

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

export const getTransactions = async (
  user_id: number,
  offset: number = 0,
  limit: number = 10,
) => {
  try {
    const response = await api.get(
      `/api/v1/transactions?user_id=${user_id}&offset=${offset}&limit=${limit}`,
    );

    const { success, error, data } = await TransactionsSchema.safeParseAsync(
      response.data,
    );

    if (!success) {
      console.error("[Get Transactions Error]", {
        message: error.message,
      });
      return [];
    }

    return data;
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Get Transactions Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return [];
  }
};

export const createTransaction = async (
  transaction: z.infer<typeof CreateTransaction>,
) => {
  const response = await api.post("/api/v1/transactions", transaction);

  const { success, error, data } = await TransactionSchema.safeParseAsync(
    response.data,
  );

  if (!success) {
    console.error("[Create Transaction Error]", {
      message: error.message,
    });
    return null;
  }

  return data;
};

// ============================================================================
// CATEGORIES
// ============================================================================

export const getCategories = async (
  offset: number = 0,
  limit: number = 100,
) => {
  try {
    const response = await api.get(
      `/api/v1/categories?offset=${offset}&limit=${limit}`,
    );

    const { success, error, data } = await CategoriesSchema.safeParseAsync(
      response.data,
    );

    if (!success) {
      console.error("[Get Categories Error]", {
        message: error.message,
      });
      return [];
    }

    return data;
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Get Categories Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return [];
  }
};

export const createCategory = async (
  name: string,
  description?: string,
  user_id?: number,
) => {
  const response = await api.post("/api/v1/categories", {
    name,
    description,
    is_default: false,
    user_id,
  });
  return response.data;
};

export const updateCategory = async (
  categoryId: number,
  name?: string,
  description?: string,
) => {
  const response = await api.patch(`/api/v1/categories/${categoryId}`, {
    name,
    description,
  });
  return response.data;
};

export const deleteCategory = async (categoryId: number) => {
  const response = await api.delete(`/api/v1/categories/${categoryId}`);
  return response.data;
};

// ============================================================================
// SOURCE ICONS
// ============================================================================

export const SOURCE_EMOJIS: Record<string, string> = {
  // Banking
  "cuenta bancaria": "🏦",
  "cuenta de ahorros": "💰",
  "cuenta corriente": "💳",
  "tarjeta de crédito": "💳",
  "tarjeta de débito": "💳",
  // Digital Wallets
  paypal: "🅿️",
  venmo: "💸",
  "cash app": "💵",
  "apple pay": "🍎",
  "google pay": "🤖",
  // Cryptocurrency
  "billetera bitcoin": "₿",
  "billetera ethereum": "Ξ",
  "exchange de cripto": "📈",
  // Investment
  "cuenta de correduría": "📊",
  "cuenta de jubilación": "👴",
  "app de inversiones": "📱",
  // Cash and Physical
  efectivo: "💵",
  cheque: "📄",
  // Business
  "cuenta empresarial": "🏢",
  "pago de cliente": "👤",
  // Other
  otro: "❓",
  desconocido: "❓",
};

// ============================================================================
// SOURCES
// ============================================================================

export const getSources = async (offset: number = 0, limit: number = 100) => {
  try {
    const response = await api.get(
      `/api/v1/sources?offset=${offset}&limit=${limit}`,
    );

    const { success, error, data } = await SourcesSchema.safeParseAsync(
      response.data,
    );

    if (!success) {
      console.error("[Get Sources Error]", {
        message: error.message,
      });
      return [];
    }

    return data;
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Get Sources Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return [];
  }
};

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
  file: { uri: string; name: string; type?: string },
  user_id: number,
  source_id: number | null = null,
  document_type: string = "photo",
) => {
  const form = new FormData();

  // Detect MIME type from file extension or use provided type
  let mimeType = file.type || "image/jpeg";
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (extension) {
    const mimeTypes: Record<string, string> = {
      jpg: "image/jpeg",
      jpeg: "image/jpeg",
      png: "image/png",
      gif: "image/gif",
      bmp: "image/bmp",
      webp: "image/webp",
      heic: "image/heic",
      heif: "image/heif",
      pdf: "application/pdf",
    };
    mimeType = mimeTypes[extension] || mimeType;
  }

  // Append file with proper format for React Native
  form.append("file", {
    uri: file.uri,
    name: file.name,
    type: mimeType,
  } as any);

  // Build query parameters
  const params = new URLSearchParams();
  params.append("user_id", user_id.toString());
  params.append("document_type", document_type);

  return api.post(
    `/api/v1/transactions/process-from-file?${params.toString()}`,
    form,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      // Longer timeout for file uploads with OCR processing
      timeout: 120000,
    },
  );
};

// ============================================================================
// AI AGENT
// ============================================================================

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
};

/**
 * Send a message to the AI ReAct agent with database access
 * The agent is scoped to only access data for the specified user
 */
export const sendAgentMessage = async (
  message: string,
  user_id: number,
  temperature?: number,
  top_p?: number,
): Promise<string> => {
  try {
    const response = await api.post("/api/v1/agents/react", {
      message,
      user_id,
      temperature,
      top_p,
    }, {
      timeout: 60000, // 60 seconds for AI responses
    });

    return response.data;
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Agent Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    throw apiError;
  }
};

// ============================================================================
// FINANCIAL HEALTH
// ============================================================================

export type FinancialHealth = {
  score: number;
  status: string;
  status_color: string;
  total_income: number;
  total_expenses: number;
  balance: number;
  savings_rate: number;
  transaction_count: number;
  top_expense_categories: { name: string; amount: number }[];
  ai_summary: string;
  ai_recommendations: string[];
  period_days: number;
};

/**
 * Get AI-powered financial health analysis for a user
 */
export const getFinancialHealth = async (
  user_id: number,
  period_days: number = 30,
): Promise<FinancialHealth | null> => {
  try {
    const response = await api.get(`/api/v1/financial-health/${user_id}`, {
      params: { period_days },
      timeout: 30000, // 30 seconds for AI analysis
    });

    return response.data;
  } catch (error) {
    const apiError = error instanceof Error ? error : parseApiError(error);
    console.error("[Financial Health Error]", {
      code: (apiError as ApiError).error_code,
      message: apiError.message,
    });
    return null;
  }
};

// ============================================================================
// NOTIFICATIONS
// ============================================================================

export type Notification = {
  id: number;
  user_id: number;
  title: string;
  body: string;
  notification_type: string;
  priority: string;
  icon: string;
  is_read: boolean;
  scheduled_at: string | null;
  action_url: string | null;
  metadata: string | null;
  created_at: string;
  updated_at: string;
};

export type NotificationStats = {
  total: number;
  unread: number;
  by_type: Record<string, number>;
};

export type CreateNotification = {
  title: string;
  body: string;
  notification_type?: string;
  priority?: string;
  icon?: string;
  scheduled_at?: string;
  action_url?: string;
};

/**
 * Get notifications for a user
 */
export const getNotifications = async (
  user_id: number,
  options?: {
    unread_only?: boolean;
    notification_type?: string;
    limit?: number;
    offset?: number;
  },
): Promise<Notification[]> => {
  try {
    const response = await api.get(`/api/v1/notifications/${user_id}`, {
      params: options,
    });
    return response.data;
  } catch (error) {
    console.error("[Notifications Error]", error);
    return [];
  }
};

/**
 * Get notification stats for a user
 */
export const getNotificationStats = async (
  user_id: number,
): Promise<NotificationStats | null> => {
  try {
    const response = await api.get(`/api/v1/notifications/${user_id}/stats`);
    return response.data;
  } catch (error) {
    console.error("[Notification Stats Error]", error);
    return null;
  }
};

/**
 * Create a new notification
 */
export const createNotification = async (
  user_id: number,
  notification: CreateNotification,
): Promise<Notification | null> => {
  try {
    const response = await api.post(`/api/v1/notifications/${user_id}`, notification);
    return response.data;
  } catch (error) {
    console.error("[Create Notification Error]", error);
    return null;
  }
};

/**
 * Create a reminder notification
 */
export const createReminder = async (
  user_id: number,
  title: string,
  body: string,
  scheduled_at?: string,
): Promise<Notification | null> => {
  try {
    const response = await api.post(`/api/v1/notifications/${user_id}/reminder`, {
      user_id,
      title,
      body,
      scheduled_at,
    });
    return response.data;
  } catch (error) {
    console.error("[Create Reminder Error]", error);
    return null;
  }
};

/**
 * Mark a notification as read
 */
export const markNotificationRead = async (
  user_id: number,
  notification_id: number,
): Promise<Notification | null> => {
  try {
    const response = await api.patch(
      `/api/v1/notifications/${user_id}/${notification_id}/read`,
    );
    return response.data;
  } catch (error) {
    console.error("[Mark Read Error]", error);
    return null;
  }
};

/**
 * Mark all notifications as read
 */
export const markAllNotificationsRead = async (
  user_id: number,
): Promise<number> => {
  try {
    const response = await api.patch(`/api/v1/notifications/${user_id}/read-all`);
    return response.data.marked_as_read;
  } catch (error) {
    console.error("[Mark All Read Error]", error);
    return 0;
  }
};

/**
 * Delete a notification
 */
export const deleteNotification = async (
  user_id: number,
  notification_id: number,
): Promise<boolean> => {
  try {
    await api.delete(`/api/v1/notifications/${user_id}/${notification_id}`);
    return true;
  } catch (error) {
    console.error("[Delete Notification Error]", error);
    return false;
  }
};

// ============================================================================
// REPORTS
// ============================================================================

export type CategoryBreakdown = {
  category_id: number;
  category_name: string;
  total_amount: number;
  percentage: number;
  transaction_count: number;
};

export type MonthlyTrend = {
  month: string;
  year: number;
  income: number;
  expenses: number;
  balance: number;
};

export type ReportData = {
  period_start: string;
  period_end: string;
  total_income: number;
  total_expenses: number;
  net_balance: number;
  savings_rate: number;
  transaction_count: number;
  category_breakdown: CategoryBreakdown[];
  monthly_trends: MonthlyTrend[];
  top_expenses: { description: string; amount: number; date: string; category_id: number }[];
  income_sources: { category_id: number; category_name: string; amount: number; percentage: number }[];
};

export type Report = {
  id: number;
  user_id: number;
  title: string;
  report_type: string;
  format: string;
  status: string;
  period_start: string;
  period_end: string;
  data: ReportData | null;
  ai_summary: string | null;
  file_path: string | null;
  created_at: string;
};

export type ReportListItem = {
  id: number;
  title: string;
  report_type: string;
  format: string;
  status: string;
  period_start: string;
  period_end: string;
  created_at: string;
};

export type GenerateReportRequest = {
  report_type: string;
  period_start: string;
  period_end: string;
  format?: string;
  title?: string;
  include_ai_summary?: boolean;
};

/**
 * Generate a new financial report
 */
export const generateReport = async (
  user_id: number,
  request: GenerateReportRequest,
): Promise<Report | null> => {
  try {
    const response = await api.post(`/api/v1/reports/${user_id}`, request, {
      timeout: 60000, // Reports may take time to generate
    });
    return response.data;
  } catch (error) {
    console.error("[Generate Report Error]", error);
    return null;
  }
};

/**
 * Generate a quick report with preset periods
 */
export const generateQuickReport = async (
  user_id: number,
  report_type: string,
  months: number = 1,
): Promise<Report | null> => {
  try {
    const response = await api.post(
      `/api/v1/reports/${user_id}/quick/${report_type}`,
      null,
      {
        params: { months },
        timeout: 60000,
      }
    );
    return response.data;
  } catch (error) {
    console.error("[Quick Report Error]", error);
    return null;
  }
};

/**
 * List reports for a user
 */
export const getReports = async (
  user_id: number,
  limit: number = 20,
  offset: number = 0,
): Promise<ReportListItem[]> => {
  try {
    const response = await api.get(`/api/v1/reports/${user_id}`, {
      params: { limit, offset },
    });
    return response.data;
  } catch (error) {
    console.error("[List Reports Error]", error);
    return [];
  }
};

/**
 * Get a specific report with full data
 */
export const getReport = async (
  user_id: number,
  report_id: number,
): Promise<Report | null> => {
  try {
    const response = await api.get(`/api/v1/reports/${user_id}/${report_id}`);
    return response.data;
  } catch (error) {
    console.error("[Get Report Error]", error);
    return null;
  }
};

/**
 * Delete a report
 */
export const deleteReport = async (
  user_id: number,
  report_id: number,
): Promise<boolean> => {
  try {
    await api.delete(`/api/v1/reports/${user_id}/${report_id}`);
    return true;
  } catch (error) {
    console.error("[Delete Report Error]", error);
    return false;
  }
};

/**
 * Get report CSV export URL
 */
export const getReportCsvUrl = (user_id: number, report_id: number): string => {
  return `${api.defaults.baseURL}/api/v1/reports/${user_id}/${report_id}/csv`;
};

export default api;
