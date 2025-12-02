import { useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  Platform,
  KeyboardAvoidingView,
  ActivityIndicator,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import {
  NotificationFeedbackType,
  notificationAsync,
  impactAsync,
  selectionAsync,
  ImpactFeedbackStyle,
} from "expo-haptics";
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withDelay,
  withSpring,
  interpolate,
} from "react-native-reanimated";
import { register } from "shared";

/**
 * Register screen
 * - Reanimated for entry + press scale
 * - Gradient button (dark: green dark->light)
 * - Haptic feedback with expo-haptics
 * - Validation: name, email, password, confirm password
 * - KeyboardAvoiding for inputs
 */

export default function RegisterScreen() {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [secure, setSecure] = useState(true);
  const [termsAccepted, setTermsAccepted] = useState(false);
  // track whether terms were auto-accepted by the form so we can distinguish manual toggles
  const [termsAutoAccepted, setTermsAutoAccepted] = useState(false);

  const [firstNameError, setFirstNameError] = useState("");
  const [lastNameError, setLastNameError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmError, setConfirmError] = useState("");
  const [termsError, setTermsError] = useState("");

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  // enabled gradient: dark mode uses darker->lighter green
  const enabledGradient: readonly [string, string] = isDark
    ? ["#062f24", theme.secondary ?? "#28a745"]
    : [theme.tint as string, theme.secondary as string];

  // reanimated shared values
  const logoProgress = useSharedValue(0);
  const formProgress = useSharedValue(0);
  const btnScale = useSharedValue(1);

  useEffect(() => {
    logoProgress.value = withTiming(1, { duration: 650 });
    formProgress.value = withDelay(120, withTiming(1, { duration: 700 }));
  }, [logoProgress, formProgress]);

  // auto-accept terms when all other fields are valid (keeps behavior optional: manual toggle still allowed)
  useEffect(() => {
    const validFields =
      firstName.trim().length > 0 &&
      lastName.trim().length > 0 &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) &&
      password.length >= 8 &&
      password === confirm;

    if (validFields && !termsAccepted) {
      setTermsAccepted(true);
      setTermsAutoAccepted(true);
      setTermsError("");
    } else if (!validFields && termsAutoAccepted) {
      // only remove the acceptance if it was auto-applied
      setTermsAccepted(false);
      setTermsAutoAccepted(false);
    }
  }, [
    firstName,
    lastName,
    email,
    password,
    confirm,
    termsAutoAccepted,
    termsAccepted,
  ]);

  const logoAnimatedStyle = useAnimatedStyle(() => ({
    opacity: logoProgress.value,
    transform: [
      { translateY: interpolate(logoProgress.value, [0, 1], [16, 0]) },
      { scale: interpolate(logoProgress.value, [0, 1], [0.98, 1]) },
    ],
  }));

  const formAnimatedStyle = useAnimatedStyle(() => ({
    opacity: formProgress.value,
    transform: [
      { translateY: interpolate(formProgress.value, [0, 1], [20, 0]) },
    ],
  }));

  const buttonAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: btnScale.value }],
  }));

  // validation helpers
  const validateEmail = (v: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);

  const validateAll = (): boolean => {
    let ok = true;
    if (!firstName.trim()) {
      setFirstNameError("Ingresa tu nombre");
      ok = false;
    } else {
      setFirstNameError("");
    }
    if (!lastName.trim()) {
      setLastNameError("Ingresa tu apellido");
      ok = false;
    } else {
      setLastNameError("");
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setEmailError("Ingresa un email válido");
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

    if (confirm !== password) {
      setConfirmError("Las contraseñas no coinciden");
      ok = false;
    } else {
      setConfirmError("");
    }

    if (!termsAccepted) {
      setTermsError("Debes aceptar los términos");
      ok = false;
    } else {
      setTermsError("");
    }

    return ok;
  };

  const isFormValid = () => {
    return (
      firstName.trim().length > 0 &&
      lastName.trim().length > 0 &&
      validateEmail(email) &&
      password.length >= 8 &&
      password === confirm &&
      termsAccepted &&
      !loading
    );
  };

  // haptics and button scale behavior
  const onPressIn = async () => {
    try {
      await selectionAsync();
    } catch {
      /* ignore */
    }
    btnScale.value = withSpring(0.97, { damping: 12, stiffness: 150 });
  };

  const onPressOut = () => {
    btnScale.value = withSpring(1, { damping: 12, stiffness: 150 });
  };

  const handleRegister = async () => {
    if (!validateAll()) {
      try {
        await notificationAsync(NotificationFeedbackType.Warning);
      } catch {}
      return;
    }

    try {
      await impactAsync(ImpactFeedbackStyle.Medium);
    } catch {}

    setLoading(true);
    setSuccess(false);

    try {
      const response = await register(
        firstName,
        lastName,
        email,
        password,
        confirm,
        termsAccepted,
      );

      if (!response) {
        await notificationAsync(NotificationFeedbackType.Error);
        return;
      }

      if (!response.success) {
        await notificationAsync(NotificationFeedbackType.Error);
        return;
      }
    } catch {
      setLoading(false);
      setSuccess(false);
      try {
        await notificationAsync(NotificationFeedbackType.Error);
      } catch {}
      return;
    }

    setLoading(false);
    setSuccess(true);
    try {
      await notificationAsync(NotificationFeedbackType.Success);
    } catch {}

    setTimeout(() => {
      router.replace("/login");
    }, 700);
  };

  return (
    <ThemedView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={styles.container}
        keyboardVerticalOffset={Platform.OS === "ios" ? 60 : 0}
      >
        {/* gradient background */}
        <LinearGradient
          colors={[theme.background, theme.inputBackground]}
          start={[0.1, 0]}
          end={[1, 1]}
          style={StyleSheet.absoluteFill}
        />

        {/* subtle accents */}
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
          <IconSymbol name="person.circle.fill" size={86} color={theme.tint} />
          <ThemedText
            type="title"
            style={[styles.title, { color: theme.tint }]}
          >
            Crear cuenta
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            Regístrate para comenzar con FinWise AI
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
          <View style={styles.rowTwo}>
            <View
              style={[
                styles.inputContainerHalf,
                {
                  borderColor: theme.icon,
                  backgroundColor: theme.inputBackground,
                },
              ]}
            >
              <IconSymbol
                name="person"
                size={18}
                color={theme.icon}
                style={styles.icon}
              />
              <TextInput
                style={[styles.input, { color: theme.text }]}
                placeholder="Nombre"
                placeholderTextColor={theme.icon}
                value={firstName}
                onChangeText={setFirstName}
                autoCapitalize="words"
                onBlur={() => {
                  if (firstName.length > 0) validateAll();
                }}
              />
            </View>

            <View
              style={[
                styles.inputContainerHalf,
                {
                  borderColor: theme.icon,
                  backgroundColor: theme.inputBackground,
                },
              ]}
            >
              <IconSymbol
                name="person"
                size={18}
                color={theme.icon}
                style={styles.icon}
              />
              <TextInput
                style={[styles.input, { color: theme.text }]}
                placeholder="Apellido"
                placeholderTextColor={theme.icon}
                value={lastName}
                onChangeText={setLastName}
                autoCapitalize="words"
                onBlur={() => {
                  if (lastName.length > 0) validateAll();
                }}
              />
            </View>
          </View>

          {firstNameError ? (
            <Text style={[styles.errorText, { color: "#d9534f" }]}>
              {firstNameError}
            </Text>
          ) : null}
          {lastNameError ? (
            <Text style={[styles.errorText, { color: "#d9534f" }]}>
              {lastNameError}
            </Text>
          ) : null}

          <View
            style={[
              styles.inputContainer,
              {
                borderColor: theme.icon,
                backgroundColor: theme.inputBackground,
              },
            ]}
          >
            <IconSymbol
              name="envelope"
              size={18}
              color={theme.icon}
              style={styles.icon}
            />
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="Email"
              placeholderTextColor={theme.icon}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              onBlur={() => {
                if (email.length > 0) validateAll();
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
                borderColor: theme.icon,
                backgroundColor: theme.inputBackground,
              },
            ]}
          >
            <IconSymbol
              name="lock"
              size={18}
              color={theme.icon}
              style={styles.icon}
            />
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="Contraseña"
              placeholderTextColor={theme.icon}
              value={password}
              onChangeText={setPassword}
              secureTextEntry={secure}
              autoCapitalize="none"
              onBlur={() => {
                if (password.length > 0) validateAll();
              }}
            />
            <Pressable onPress={() => setSecure((s) => !s)} hitSlop={8}>
              <IconSymbol
                name={secure ? "eye.slash" : "eye"}
                size={16}
                color={theme.icon}
                style={{ marginLeft: 8 }}
              />
            </Pressable>
          </View>
          {passwordError ? (
            <Text style={[styles.errorText, { color: "#d9534f" }]}>
              {passwordError}
            </Text>
          ) : null}

          <View
            style={[
              styles.inputContainer,
              {
                borderColor: theme.icon,
                backgroundColor: theme.inputBackground,
              },
            ]}
          >
            <IconSymbol
              name="checkmark"
              size={18}
              color={theme.icon}
              style={styles.icon}
            />
            <TextInput
              style={[styles.input, { color: theme.text }]}
              placeholder="Confirmar contraseña"
              placeholderTextColor={theme.icon}
              value={confirm}
              onChangeText={setConfirm}
              secureTextEntry={true}
              autoCapitalize="none"
              onBlur={() => {
                if (confirm.length > 0) validateAll();
              }}
            />
          </View>
          {confirmError ? (
            <Text style={[styles.errorText, { color: "#d9534f" }]}>
              {confirmError}
            </Text>
          ) : null}

          <View style={styles.rowBetween}>
            <Pressable onPress={() => router.replace("/login")}>
              <Text style={[styles.linkText, { color: theme.icon }]}>
                Tengo cuenta
              </Text>
            </Pressable>
            <Pressable
              onPress={() => {
                setFirstName("");
                setLastName("");
                setEmail("");
                setPassword("");
                setConfirm("");
                setTermsAccepted(false);
              }}
            >
              <Text style={[styles.linkText, { color: theme.tint }]}>
                Limpiar
              </Text>
            </Pressable>
          </View>

          <Pressable
            onPressIn={onPressIn}
            onPressOut={onPressOut}
            onPress={() => {
              if (!loading && isFormValid()) {
                handleRegister();
              } else {
                // invalid press feedback
                try {
                  notificationAsync(NotificationFeedbackType.Warning);
                } catch {}
                validateAll();
              }
            }}
            accessibilityRole="button"
            accessibilityState={{ disabled: !isFormValid() || loading }}
            style={{ width: "100%" }}
          >
            <Animated.View style={[styles.buttonWrapper, buttonAnimatedStyle]}>
              {isFormValid() ? (
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
                        color="#fff"
                        style={{ marginRight: 8 }}
                      />
                    ) : success ? (
                      <IconSymbol
                        name="checkmark.circle.fill"
                        size={18}
                        color="#fff"
                        style={{ marginRight: 8 }}
                      />
                    ) : null}
                    <Text style={[styles.buttonText, { color: "#fff" }]}>
                      {loading
                        ? "Registrando..."
                        : success
                          ? "Listo"
                          : "Crear cuenta"}
                    </Text>
                  </View>
                </LinearGradient>
              ) : (
                <View
                  style={[
                    styles.buttonDisabled,
                    {
                      backgroundColor: isDark ? "#222" : "#e6f2ff",
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
                    Crear cuenta
                  </Text>
                </View>
              )}
            </Animated.View>
          </Pressable>

          <View style={styles.footerNote}>
            <Pressable
              style={{
                flexDirection: "row",
                alignItems: "center",
                marginBottom: 8,
              }}
              onPress={() => {
                // if acceptance was auto-applied, clear auto flag when user manually toggles
                if (termsAutoAccepted) {
                  setTermsAutoAccepted(false);
                }
                setTermsAccepted((t) => !t);
                setTermsError("");
              }}
              hitSlop={8}
            >
              <View
                style={[
                  styles.checkbox,
                  {
                    borderColor: theme.icon,
                    backgroundColor: termsAccepted
                      ? theme.tint
                      : theme.inputBackground,
                  },
                ]}
              >
                {termsAccepted ? (
                  <IconSymbol name="checkmark" size={14} color="#fff" />
                ) : null}
              </View>
              <Text
                style={[
                  styles.footerText,
                  { color: theme.icon, marginLeft: 10 },
                ]}
              >
                Acepto los términos y condiciones
              </Text>
            </Pressable>

            <Text style={[styles.footerText, { color: theme.icon }]}>
              Al registrarte aceptas los términos y condiciones.
            </Text>
            {termsError ? (
              <Text
                style={[
                  styles.errorText,
                  { color: "#d9534f", textAlign: "center" },
                ]}
              >
                {termsError}
              </Text>
            ) : null}
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
    padding: 20,
    position: "relative",
  },
  accent: {
    position: "absolute",
    width: 300,
    height: 300,
    borderRadius: 150,
    top: -60,
    right: -80,
    transform: [{ rotate: "22deg" }],
  },
  accentSmall: {
    position: "absolute",
    width: 160,
    height: 160,
    borderRadius: 80,
    bottom: -40,
    left: -50,
  },
  logoContainer: {
    alignItems: "center",
    marginBottom: 18,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    marginTop: 10,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    textAlign: "center",
  },
  formContainer: {
    padding: 18,
    borderRadius: 16,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: Platform.OS === "ios" ? 0.12 : 0.18,
    shadowRadius: 10,
    elevation: 10,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  inputContainerHalf: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: 12,
    marginBottom: 12,
    paddingHorizontal: 12,
    paddingVertical: 6,
    flex: 1,
    marginRight: 8,
  },
  rowTwo: {
    flexDirection: "row",
    width: "100%",
    marginBottom: 8,
  },
  icon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    height: 46,
    fontSize: 15,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  linkText: {
    fontSize: 13,
  },
  buttonWrapper: {
    width: "100%",
  },
  button: {
    borderRadius: 12,
    alignItems: "center",
    marginTop: 10,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.22,
    shadowRadius: 8,
    elevation: 6,
  },
  btnContent: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  buttonDisabled: {
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#c0c8d9",
    marginTop: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "700",
  },
  footerNote: {
    marginTop: 14,
    alignItems: "center",
  },
  footerText: {
    fontSize: 12,
    textAlign: "center",
  },
  errorText: {
    marginTop: 6,
    marginBottom: 6,
    fontSize: 13,
    color: "#d9534f",
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: "#c0c8d9",
    alignItems: "center",
    justifyContent: "center",
  },
});
