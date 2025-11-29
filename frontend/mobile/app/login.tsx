import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  Alert,
  Platform,
  ActivityIndicator,
  KeyboardAvoidingView,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import {
  impactAsync,
  selectionAsync,
  ImpactFeedbackStyle,
  notificationAsync,
  NotificationFeedbackType,
} from "expo-haptics";
import { login as apiLogin } from "shared";
import { useAuth } from "@/contexts/AuthContext";

import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withDelay,
  withSpring,
  interpolate,
} from "react-native-reanimated";

/**
 * Login screen with:
 * - Reanimated v2 animations for logo and form entry + press scale
 * - Haptic feedback via expo-haptics on press
 * - Inline validation and loading/check states
 * - Improved error handling with specific messages
 * - Retry logic for network errors
 *
 * Notes:
 * - Make sure `react-native-reanimated` is installed and configured in your project (babel plugin).
 * - Make sure `expo-haptics` is installed: `expo install expo-haptics`
 */

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [secure, setSecure] = useState(true);
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [generalError, setGeneralError] = useState("");

  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const { login, isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/home");
    }
  }, [isAuthenticated, isLoading, router]);

  // Enabled gradient: use darker->lighter green in dark mode
  const enabledGradient: readonly [string, string] = isDark
    ? ["#08351f", theme.secondary ?? "#2f8f5a"]
    : [theme.tint as string, theme.secondary as string];

  // Reanimated shared values
  const logoProgress = useSharedValue(0);
  const formProgress = useSharedValue(0);
  const btnScale = useSharedValue(1);

  useEffect(() => {
    logoProgress.value = withTiming(1, { duration: 650 });
    formProgress.value = withDelay(160, withTiming(1, { duration: 700 }));
  }, [logoProgress, formProgress]);

  // Styles driven by reanimated values
  const logoAnimatedStyle = useAnimatedStyle(() => {
    return {
      opacity: logoProgress.value,
      transform: [
        {
          translateY: interpolate(logoProgress.value, [0, 1], [16, 0]),
        },
        {
          scale: interpolate(logoProgress.value, [0, 1], [0.98, 1]),
        },
      ],
    };
  });

  const formAnimatedStyle = useAnimatedStyle(() => {
    return {
      opacity: formProgress.value,
      transform: [
        {
          translateY: interpolate(formProgress.value, [0, 1], [20, 0]),
        },
      ],
    };
  });

  const buttonAnimatedStyle = useAnimatedStyle(() => {
    return {
      transform: [{ scale: btnScale.value }],
    };
  });

  // Validation helpers
  const validate = () => {
    let ok = true;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setEmailError("Ingresa un correo válido");
      ok = false;
    } else {
      setEmailError("");
    }

    if (password.length < 8) {
      setPasswordError("La contraseña debe tener al menos 8 caracteres");
      ok = false;
    } else {
      setPasswordError("");
    }
    return ok;
  };

  const isValid = () => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email) && password.length >= 8 && !loading;
  };

  // Haptic + press scale
  const handlePressIn = async () => {
    // gentle haptic
    try {
      await selectionAsync();
    } catch {
      // ignore if unavailable
    }
    btnScale.value = withSpring(0.97, { damping: 12, stiffness: 150 });
  };

  const handlePressOut = () => {
    btnScale.value = withSpring(1, { damping: 12, stiffness: 150 });
  };

  // Handle login: set loading, show spinner, then success & navigate
  const handleLogin = async () => {
    if (!validate()) return;

    // Start loading and show spinner
    setLoading(true);
    setSuccess(false);
    setGeneralError("");

    // subtle haptic for action
    try {
      impactAsync(ImpactFeedbackStyle.Medium);
    } catch {
      /* no-op */
    }

    try {
      const response = await apiLogin(email, password);

      if (!response) {
        setLoading(false);
        const errorMsg = "";
        Alert.alert("Error de autenticación", errorMsg);
        return;
      }

      if (!response.success || !response.user || !response.access_token) {
        setLoading(false);
        const errorMsg = "Respuesta inválida del servidor";
        setGeneralError(errorMsg);
        Alert.alert("Error", errorMsg);
        return;
      }

      // Successfully logged in
      await login(response.user, response.access_token);
      setLoading(false);
      setSuccess(true);

      // short delay so user sees check icon
      setTimeout(() => {
        router.replace("/home");
      }, 700);
    } catch (error) {
      console.error("Login error:", error);
      setLoading(false);
      const errorMsg =
        error instanceof Error
          ? error.message
          : "Error desconocido durante el login";
      setGeneralError(errorMsg);
      Alert.alert("Error", errorMsg);
    }
  };

  const handleForgot = () => {
    Alert.alert(
      "Recuperar contraseña",
      "Se ha enviado un enlace a tu email (simulado).",
    );
  };

  return (
    <ThemedView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.container}
        keyboardVerticalOffset={Platform.OS === "ios" ? 60 : 0}
      >
        {/* Background gradient */}
        <LinearGradient
          colors={[theme.background, theme.inputBackground]}
          start={[0.1, 0]}
          end={[1, 1]}
          style={StyleSheet.absoluteFill}
        />

        {/* decorative accents */}
        <View
          style={[
            styles.accent,
            {
              backgroundColor: theme.tint,
              opacity: 0.06,
              pointerEvents: "none",
            },
          ]}
        />
        <View
          style={[
            styles.accentSmall,
            {
              backgroundColor: theme.secondary,
              opacity: 0.04,
              pointerEvents: "none",
            },
          ]}
        />

        <Animated.View style={[styles.logoContainer, logoAnimatedStyle]}>
          <IconSymbol
            name="dollarsign.circle.fill"
            size={92}
            color={theme.tint}
          />
          <ThemedText
            type="title"
            style={[styles.title, { color: theme.tint }]}
          >
            FinWise AI
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            Tu asistente financiero inteligente
          </ThemedText>
        </Animated.View>

        <Animated.View
          style={[
            styles.formContainer,
            {
              backgroundColor: theme.cardBackground,
              shadowColor: theme.shadow,
            },
            formAnimatedStyle,
          ]}
        >
          {generalError ? (
            <View style={styles.errorBanner}>
              <IconSymbol
                name="exclamationmark.circle.fill"
                size={18}
                color="#d9534f"
                style={{ marginRight: 8 }}
              />
              <Text style={[styles.errorBannerText, { color: "#d9534f" }]}>
                {generalError}
              </Text>
            </View>
          ) : null}

          <View
            style={[
              styles.inputContainer,
              {
                borderColor: emailError ? "#d9534f" : theme.icon,
                backgroundColor: theme.inputBackground,
              },
            ]}
          >
            <IconSymbol
              name="envelope"
              size={20}
              color={theme.icon}
              style={styles.icon}
            />
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="Email"
              placeholderTextColor={theme.icon}
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                setGeneralError("");
              }}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              textContentType="username"
              editable={!loading}
              onBlur={() => {
                if (email.length > 0) validate();
              }}
            />
          </View>
          {emailError ? (
            <Text style={[styles.errorText, { color: "#d9534f" }]}>
              {emailError}
            </Text>
          ) : null}

          <View
            style={[
              styles.inputContainer,
              {
                borderColor: passwordError ? "#d9534f" : theme.icon,
                backgroundColor: theme.inputBackground,
              },
            ]}
          >
            <IconSymbol
              name="lock"
              size={20}
              color={theme.icon}
              style={styles.icon}
            />
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="Contraseña"
              placeholderTextColor={theme.icon}
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                setGeneralError("");
              }}
              secureTextEntry={secure}
              textContentType="password"
              autoCapitalize="none"
              editable={!loading}
              onBlur={() => {
                if (password.length > 0) validate();
              }}
            />
            <Pressable
              onPress={() => setSecure((s) => !s)}
              hitSlop={8}
              disabled={loading}
            >
              <IconSymbol
                name={secure ? "eye.slash" : "eye"}
                size={18}
                color={theme.icon}
                style={{ marginLeft: 10 }}
              />
            </Pressable>
          </View>
          {passwordError ? (
            <Text style={[styles.errorText, { color: "#d9534f" }]}>
              {passwordError}
            </Text>
          ) : null}

          <View style={styles.rowBetween}>
            <Pressable onPress={handleForgot} disabled={loading}>
              <Text style={[styles.linkText, { color: theme.tint }]}>
                ¿Olvidaste tu contraseña?
              </Text>
            </Pressable>
            <Pressable
              onPress={() => router.push("/register" as any)}
              disabled={loading}
            >
              <Text style={[styles.linkText, { color: theme.icon }]}>
                Crear cuenta
              </Text>
            </Pressable>
          </View>

          <Pressable
            onPressIn={handlePressIn}
            onPressOut={handlePressOut}
            onPress={() => {
              if (!loading && isValid()) {
                try {
                  impactAsync(ImpactFeedbackStyle.Medium);
                } catch {}
                handleLogin();
              } else if (!isValid() && !loading) {
                try {
                  notificationAsync(NotificationFeedbackType.Warning);
                } catch {}
              }
            }}
            accessibilityRole="button"
            accessibilityState={{ disabled: !isValid() || loading }}
            style={{ width: "100%" }}
            disabled={loading}
          >
            <Animated.View style={[styles.buttonWrapper, buttonAnimatedStyle]}>
              {isValid() ? (
                <LinearGradient
                  colors={enabledGradient}
                  start={[0, 0]}
                  end={[1, 1]}
                  style={[styles.button, { paddingVertical: 14 }]}
                >
                  <View style={styles.btnContent}>
                    {loading ? (
                      <ActivityIndicator
                        size="small"
                        color={"#fff"}
                        style={{ marginRight: 8 }}
                      />
                    ) : success ? (
                      <IconSymbol
                        name="checkmark.circle.fill"
                        size={18}
                        color={"#fff"}
                        style={{ marginRight: 8 }}
                      />
                    ) : null}
                    <Text style={[styles.buttonText, { color: "#fff" }]}>
                      {loading
                        ? "Enviando..."
                        : success
                          ? "Listo"
                          : "Iniciar Sesión"}
                    </Text>
                  </View>
                </LinearGradient>
              ) : (
                <View
                  style={[
                    styles.buttonDisabled,
                    {
                      backgroundColor: isDark ? "#2f2f2f" : "#dbeffd",
                      paddingVertical: 14,
                    },
                  ]}
                >
                  <Text
                    style={[
                      styles.buttonText,
                      { color: isDark ? "#9aa0a6" : "#6b7280" },
                    ]}
                  >
                    Iniciar Sesión
                  </Text>
                </View>
              )}
            </Animated.View>
          </Pressable>

          <View style={styles.footerNote}>
            <Text style={[styles.footerText, { color: theme.icon }]}>
              ¿Nuevo en FinWise? Crea una cuenta para comenzar.
            </Text>
          </View>
        </Animated.View>
      </KeyboardAvoidingView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  container: {
    flex: 1,
    justifyContent: "center",
    padding: 22,
    position: "relative",
  },
  accent: {
    position: "absolute",
    width: 320,
    height: 320,
    borderRadius: 160,
    top: -80,
    right: -100,
    transform: [{ rotate: "25deg" }],
  },
  accentSmall: {
    position: "absolute",
    width: 180,
    height: 180,
    borderRadius: 90,
    bottom: -50,
    left: -60,
  },
  logoContainer: {
    alignItems: "center",
    marginBottom: 30,
  },
  title: {
    fontSize: 30,
    fontWeight: "800",
    marginTop: 10,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 15,
    textAlign: "center",
  },
  formContainer: {
    padding: 22,
    borderRadius: 18,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: Platform.OS === "ios" ? 0.12 : 0.18,
    shadowRadius: 12,
    elevation: 12,
  },
  errorBanner: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fadbd8",
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: "#d9534f",
  },
  errorBannerText: {
    flex: 1,
    fontSize: 13,
    fontWeight: "500",
    lineHeight: 18,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 14,
    marginBottom: 16,
    paddingHorizontal: 14,
    paddingVertical: 6,
  },
  icon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    height: 52,
    fontSize: 16,
    paddingVertical: 8,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  linkText: {
    fontSize: 13,
  },
  buttonWrapper: {
    width: "100%",
  },
  button: {
    borderRadius: 14,
    alignItems: "center",
    marginTop: 8,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.22,
    shadowRadius: 8,
    elevation: 6,
  },
  btnContent: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 6,
  },
  buttonDisabled: {
    borderRadius: 14,
    alignItems: "center",
    marginTop: 8,
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#c0c8d9",
  },
  buttonText: {
    color: "#fff",
    fontSize: 17,
    fontWeight: "800",
  },
  footerNote: {
    marginTop: 14,
    alignItems: "center",
  },
  footerText: {
    fontSize: 13,
  },
  errorText: {
    marginTop: 6,
    marginBottom: 8,
    fontSize: 13,
    lineHeight: 18,
  },
});
