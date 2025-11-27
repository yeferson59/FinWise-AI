import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
  useCallback,
} from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";

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

  const decodeToken = useCallback((token: string): DecodedToken | null => {
    try {
      // Simple JWT decode without verification (signature verified by backend)
      const parts = token.split(".");
      if (parts.length !== 3) return null;

      const payload = JSON.parse(atob(parts[1]));
      return payload as DecodedToken;
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
            // Validate user data structure
            if (
              parsedUser.id &&
              parsedUser.email &&
              parsedUser.first_name &&
              parsedUser.last_name
            ) {
              setUser(parsedUser);
              setToken(storedToken);
            } else {
              // Invalid user data, clear storage
              await AsyncStorage.removeItem("user");
              await AsyncStorage.removeItem("token");
            }
          } else {
            // Invalid token, clear storage
            await AsyncStorage.removeItem("user");
            await AsyncStorage.removeItem("token");
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
    setUser(null);
    setToken(null);
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
    if (!token || isTokenExpired()) {
      await logout();
      return false;
    }
    return true;
  }, [token, isTokenExpired, logout]);

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
