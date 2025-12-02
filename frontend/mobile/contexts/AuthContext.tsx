import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AppState, AppStateStatus } from "react-native";
import { decode as base64Decode } from "base-64";
import { logout as apiLogout, setAuthToken } from "shared";

interface User {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

interface DecodedToken {
  sub: string;
  email?: string;
  exp?: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
  isAuthenticated: boolean;
  refreshToken: () => Promise<boolean>;
  isTokenExpired: () => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_CHECK_INTERVAL = 2 * 60 * 1000;

const normalizeBase64Segment = (segment: string) => {
  const normalized = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padding = normalized.length % 4 === 0 ? 0 : 4 - (normalized.length % 4);
  return normalized + "=".repeat(padding);
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const appStateRef = useRef<AppStateStatus>(
    AppState.currentState as AppStateStatus,
  );

  /**
   * Decode a JWT token payload safely
   */
  const decodeToken = useCallback((rawToken: string): DecodedToken | null => {
    try {
      const parts = rawToken.split(".");
      if (parts.length !== 3) return null;

      const payloadSegment = normalizeBase64Segment(parts[1]);
      const decodedPayload = base64Decode(payloadSegment);
      return JSON.parse(decodedPayload) as DecodedToken;
    } catch (error) {
      console.error("Error decoding token:", error);
      return null;
    }
  }, []);

  /**
   * Check if token is expired
   */
  const isTokenExpired = useCallback((): boolean => {
    if (!token) return true;

    const decoded = decodeToken(token);
    if (!decoded || !decoded.exp) return false;

    // Add 60 second buffer to catch expiration early
    const expirationTime = decoded.exp * 1000 - 60000;
    return Date.now() > expirationTime;
  }, [token, decodeToken]);

  /**
   * Save user and token to state and storage
   */
  const login = useCallback(
    async (userData: User, authToken: string) => {
      try {
        // Validate token structure
        const decoded = decodeToken(authToken);
        if (!decoded) {
          throw new Error("Invalid token format");
        }

        if (decoded.exp && decoded.exp * 1000 <= Date.now()) {
          throw new Error("El token ha expirado, inicia sesión nuevamente.");
        }

        // Validate user data
        if (
          !userData.id ||
          !userData.email ||
          !userData.first_name ||
          !userData.last_name
        ) {
          throw new Error("Invalid user data");
        }

        setUser(userData);
        setToken(authToken);

        await Promise.all([
          AsyncStorage.setItem("user", JSON.stringify(userData)),
          AsyncStorage.setItem("token", authToken),
        ]);

        // Set token for API requests
        setAuthToken(authToken);
      } catch (error) {
        console.error("Error storing auth data:", error);
        throw error;
      }
    },
    [decodeToken],
  );

  /**
   * Clear user and token
   */
  const logout = useCallback(async () => {
    try {
      // Call logout API to invalidate session on server
      await apiLogout();
    } catch (error) {
      console.error("Error calling logout API:", error);
      // Continue with local logout even if API call fails
    }

    setUser(null);
    setToken(null);

    // Clear token from API requests
    setAuthToken(null);

    try {
      await Promise.all([
        AsyncStorage.removeItem("user"),
        AsyncStorage.removeItem("token"),
      ]);
    } catch (error) {
      console.error("Error removing auth data:", error);
    }
  }, []);

  /**
   * Attempt to refresh token
   * This would typically call a refresh endpoint
   * For now, we return false if token is expired
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    if (!token) {
      return false;
    }

    if (isTokenExpired()) {
      await logout();
      return false;
    }

    return true;
  }, [token, isTokenExpired, logout]);

  /**
   * Load stored auth data on mount
   */
  useEffect(() => {
    const loadStoredAuth = async () => {
      try {
        const storedUser = await AsyncStorage.getItem("user");
        const storedToken = await AsyncStorage.getItem("token");

        if (storedUser && storedToken) {
          const parsedUser = JSON.parse(storedUser);

          // Check if token is valid
          const decoded = decodeToken(storedToken);
          if (decoded) {
            const isExpired = decoded.exp
              ? decoded.exp * 1000 <= Date.now()
              : false;

            if (isExpired) {
              await AsyncStorage.removeItem("user");
              await AsyncStorage.removeItem("token");
              setAuthToken(null);
            } else if (
              parsedUser.id &&
              parsedUser.email &&
              parsedUser.first_name &&
              parsedUser.last_name
            ) {
              setUser(parsedUser);
              setToken(storedToken);
              setAuthToken(storedToken);
            } else {
              // Invalid user data, clear storage
              await AsyncStorage.removeItem("user");
              await AsyncStorage.removeItem("token");
              setAuthToken(null);
            }
          } else {
            // Invalid token, clear storage
            await AsyncStorage.removeItem("user");
            await AsyncStorage.removeItem("token");
            setAuthToken(null);
          }
        }
      } catch (error) {
        console.error("Error loading auth data:", error);
        // Clear potentially corrupted data
        await AsyncStorage.removeItem("user");
        await AsyncStorage.removeItem("token");
      } finally {
        setIsLoading(false);
      }
    };

    loadStoredAuth();
  }, [decodeToken]);

  /**
   * If token is expired after load, log out
   */
  useEffect(() => {
    if (isLoading) return;
    if (token && isTokenExpired()) {
      // logout is declared above, safe to call
      logout();
    }
  }, [isLoading, token, isTokenExpired, logout]);

  /**
   * Refresh token when app comes to foreground
   */
  useEffect(() => {
    const handleAppStateChange = (nextState: AppStateStatus) => {
      const wasBackground =
        appStateRef.current === "background" ||
        appStateRef.current === "inactive";

      if (wasBackground && nextState === "active") {
        // refreshToken is declared above
        refreshToken();
      }

      appStateRef.current = nextState;
    };

    const subscription = AppState.addEventListener(
      "change",
      handleAppStateChange,
    );
    return () => subscription.remove();
  }, [refreshToken]);

  /**
   * Periodically check token validity
   */
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(() => {
      refreshToken();
    }, TOKEN_CHECK_INTERVAL);
    return () => clearInterval(interval);
  }, [token, refreshToken]);

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isLoading,
    isAuthenticated: !!user && !!token && !isTokenExpired(),
    refreshToken,
    isTokenExpired,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
