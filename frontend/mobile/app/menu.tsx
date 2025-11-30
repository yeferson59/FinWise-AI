import React, { useEffect, useRef } from "react";
import {
  Animated,
  View,
  Pressable,
  StyleSheet,
  ScrollView,
  Text,
  Alert,
} from "react-native";
import { useRouter } from "expo-router";
import {
  useSafeAreaInsets,
  SafeAreaView,
} from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useNotificationContext } from "@/contexts/NotificationContext";

/**
 * Side menu screen
 * - Presents routes / quick links that reflect backend use-cases from backend/README.md
 * - Adapts to light/dark themes used across the app
 *
 * Routes (example):
 * - Perfil (users & auth)
 * - Asistente (IA)
 * - OCR (subida / reconocimiento)
 * - Transacciones (CRUD / filtros)
 * - Categorías
 * - Reportes
 * - Presupuestos
 * - Integraciones (bancarias / cuentas)
 * - Notificaciones
 * - Ajustes
 * - Cerrar sesión
 *
 * This file only creates navigation links. Replace routes with actual paths in your app
 * if they differ.
 */

type RouteName =
  | "/profile"
  | "/assistant"
  | "/ocr"
  | "/audio-transaction"
  | "/transactions"
  | "/transactions/new"
  | "/categories"
  | "/reports"
  | "/budget"
  | "/integrations"
  | "/notifications"
  | "/settings"
  | "/home"
  | "/login";

const MENU_ITEMS: {
  id: string;
  title: string;
  subtitle?: string;
  route?: RouteName;
  icon?: string;
}[] = [
  {
    id: "profile",
    title: "Perfil",
    subtitle: "Cuenta y seguridad",
    route: "/profile",
    icon: "👤",
  },
  {
    id: "assistant",
    title: "Asistente IA",
    subtitle: "Responde preguntas y ayuda con finanzas",
    route: "/assistant",
    icon: "✨",
  },
  {
    id: "ocr",
    title: "OCR",
    subtitle: "Escanear recibos y facturas",
    route: "/ocr",
    icon: "📷",
  },
  {
    id: "audio",
    title: "Voz a Transacción",
    subtitle: "Dicta y crea transacciones por voz",
    route: "/audio-transaction",
    icon: "🎤",
  },
  {
    id: "transactions",
    title: "Transacciones",
    subtitle: "Ver, crear y filtrar movimientos",
    route: "/transactions",
    icon: "📋",
  },
  {
    id: "categories",
    title: "Categorías",
    subtitle: "Administrar categorías y etiquetas",
    route: "/categories",
    icon: "🏷️",
  },
  {
    id: "reports",
    title: "Reportes",
    subtitle: "Informes y exportación (PDF)",
    route: "/reports",
    icon: "📄",
  },
  {
    id: "budgets",
    title: "Presupuestos",
    subtitle: "Crear y seguir presupuestos",
    route: "/budget",
    icon: "💰",
  },
  {
    id: "integrations",
    title: "Integraciones",
    subtitle: "Bancos y multi-moneda (próximamente)",
    route: "/integrations",
    icon: "🔗",
  },
  {
    id: "notifications",
    title: "Notificaciones",
    subtitle: "Recordatorios y alertas",
    route: "/notifications",
    icon: "🔔",
  },
  {
    id: "settings",
    title: "Ajustes",
    subtitle: "Preferencias de la aplicación",
    route: "/settings",
    icon: "⚙️",
  },
];

export default function MenuScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { unreadCount } = useNotificationContext();

  // entry animation for the menu: fade + slide up
  const anim = useRef(new Animated.Value(0));
  useEffect(() => {
    Animated.timing(anim.current, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start();
  }, []);

  const handleNavigate = (route?: RouteName) => {
    if (!route) return;

    // Animate out then navigate so the menu feels like a drawer
    Animated.timing(anim.current, {
      toValue: 0,
      duration: 180,
      useNativeDriver: true,
    }).start(() => {
      // Use explicit route cases so we only pass literal route strings to the router API.
      // Cast to `any` when calling router methods to satisfy the router typings for now.
      switch (route) {
        case "/profile":
          try {
            router.replace("/profile" as any);
          } catch {
            router.replace("/profile" as any);
          }
          break;
        case "/assistant":
          try {
            router.replace("/assistant" as any);
          } catch {
            router.replace("/assistant" as any);
          }
          break;
        case "/ocr":
          try {
            router.replace("/ocr" as any);
          } catch {
            router.replace("/ocr" as any);
          }
          break;
        case "/audio-transaction":
          try {
            router.replace("/audio-transaction" as any);
          } catch {
            router.replace("/audio-transaction" as any);
          }
          break;
        case "/transactions":
          try {
            router.replace("/transactions" as any);
          } catch {
            router.replace("/transactions" as any);
          }
          break;
        case "/transactions/new":
          try {
            router.replace("/transactions/new" as any);
          } catch {
            router.replace("/transactions/new" as any);
          }
          break;
        case "/categories":
          try {
            router.replace("/categories" as any);
          } catch {
            router.replace("/categories" as any);
          }
          break;
        case "/reports":
          try {
            router.replace("/reports" as any);
          } catch {
            router.replace("/reports" as any);
          }
          break;
        case "/budget":
          try {
            router.replace("/budget" as any);
          } catch {
            router.replace("/budget" as any);
          }
          break;
        case "/integrations":
          try {
            router.replace("/integrations" as any);
          } catch {
            router.replace("/integrations" as any);
          }
          break;
        case "/notifications":
          try {
            router.replace("/notifications" as any);
          } catch {
            router.replace("/notifications" as any);
          }
          break;
        case "/settings":
          try {
            router.replace("/settings" as any);
          } catch {
            router.replace("/settings" as any);
          }
          break;
        case "/home":
          try {
            router.replace("/home" as any);
          } catch {
            router.replace("/home" as any);
          }
          break;
        case "/login":
          try {
            router.replace("/login" as any);
          } catch {
            router.replace("/login" as any);
          }
          break;
        default:
          // fallback to home if an unknown route somehow arrives
          router.replace("/home" as any);
          break;
      }
    });
  };

  const handleLogout = () => {
    Alert.alert("Cerrar sesión", "¿Deseas cerrar sesión?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Cerrar sesión",
        style: "destructive",
        onPress: () => {
          router.replace("/login" as any);
        },
      },
    ]);
  };

  return (
    <ThemedView style={[styles.root, { backgroundColor: theme.background }]}>
      <SafeAreaView style={{ flex: 1 }}>
        <Animated.View
          style={{
            opacity: anim.current,
            transform: [
              {
                translateY: anim.current.interpolate({
                  inputRange: [0, 1],
                  outputRange: [8, 0],
                }),
              },
            ],
          }}
        >
          <ScrollView
            contentContainerStyle={[
              styles.container,
              { paddingTop: insets.top + 10 },
            ]}
            showsVerticalScrollIndicator={false}
          >
            <View style={styles.headerRow}>
              <View>
                <ThemedText
                  type="title"
                  style={[styles.headerTitle, { color: theme.text }]}
                >
                  Menú
                </ThemedText>
                <ThemedText
                  style={[styles.headerSubtitle, { color: theme.icon }]}
                >
                  Accesos rápidos
                </ThemedText>
              </View>

              <Pressable
                onPress={() => router.back()}
                style={[
                  styles.closeButton,
                  {
                    backgroundColor: isDark ? "#2b2b2b" : theme.cardBackground,
                    ...createShadow(0, 4, 8, theme.shadow, 6),
                  },
                ]}
                hitSlop={8}
              >
                <Text style={{ fontSize: 18, color: theme.icon }}>✕</Text>
              </Pressable>
            </View>

            <Pressable
              onPress={() => handleNavigate("/home")}
              style={styles.featuredWrapper}
            >
              <LinearGradient
                colors={
                  isDark ? ["#0f172a", "#0f766e"] : ["#7dd3fc", "#2563eb"]
                }
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.featuredCard}
              >
                <View style={styles.featuredContent}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.featuredTitle}>Volver al inicio</Text>
                    <Text style={styles.featuredSubtitle}>
                      Revisa tu panel y métricas principales en segundos.
                    </Text>
                    <View style={styles.featuredBadge}>
                      <Text style={styles.featuredBadgeText}>Dashboard</Text>
                    </View>
                  </View>
                  <View style={styles.featuredIcon}>
                    <IconSymbol name={"house.fill" as any} size={32} color="#fff" />
                  </View>
                </View>
              </LinearGradient>
            </Pressable>

            <View style={styles.section}>
              {MENU_ITEMS.map((m) => (
                <Pressable
                  key={m.id}
                  onPress={() => handleNavigate(m.route)}
                  style={({ pressed }) => [
                    styles.menuRow,
                    {
                      backgroundColor: pressed
                        ? isDark
                          ? "#232323"
                          : "#f5f7fb"
                        : theme.cardBackground,
                      borderColor: isDark
                        ? "rgba(255,255,255,0.03)"
                        : "transparent",
                      ...createShadow(0, 4, 8, theme.shadow, 4),
                    },
                  ]}
                >
                  <View style={styles.menuLeft}>
                    <View
                      style={[
                        styles.iconBox,
                        {
                          backgroundColor: isDark
                            ? "rgba(255,255,255,0.02)"
                            : "#f1fbff",
                        },
                      ]}
                    >
                      <Text style={{ fontSize: 18, color: theme.tint }}>
                        {m.icon}
                      </Text>
                    </View>
                    <View style={{ marginLeft: 12 }}>
                      <Text style={[styles.menuTitle, { color: theme.text }]}>
                        {m.title}
                      </Text>
                      {m.subtitle ? (
                        <Text
                          style={[styles.menuSubtitle, { color: theme.icon }]}
                        >
                          {m.subtitle}
                        </Text>
                      ) : null}
                    </View>
                  </View>

                  <View style={styles.menuRight}>
                    {/* Show notification badge for notifications item */}
                    {m.id === "notifications" && unreadCount > 0 && (
                      <View style={styles.notificationBadge}>
                        <Text style={styles.notificationBadgeText}>
                          {unreadCount > 99 ? "99+" : unreadCount}
                        </Text>
                      </View>
                    )}
                    <Text style={{ fontSize: 18, color: theme.icon }}>›</Text>
                  </View>
                </Pressable>
              ))}
            </View>

            <View style={styles.section}>
              <Pressable
                onPress={() => handleNavigate("/transactions/new")}
                style={({ pressed }) => [
                  styles.logoutRow,
                  {
                    backgroundColor: pressed ? "#2b2b2b" : "#dc3545",
                    ...createShadow(0, 4, 8, theme.shadow, 4),
                  },
                ]}
              >
                <Text style={{ fontSize: 18, color: theme.tint }}>+</Text>
                <Text style={[styles.actionLabel, { color: theme.text }]}>
                  Añadir transacción
                </Text>
              </Pressable>

              <Pressable
                onPress={() => handleNavigate("/reports")}
                style={({ pressed }) => [
                  styles.actionButton,
                  {
                    backgroundColor: pressed
                      ? theme.inputBackground
                      : theme.cardBackground,
                    borderColor: isDark
                      ? "rgba(255,255,255,0.03)"
                      : "transparent",
                    ...createShadow(0, 4, 8, theme.shadow, 4),
                  },
                ]}
              >
                <Text style={{ fontSize: 18, color: theme.tint }}>📄</Text>
                <Text style={[styles.actionLabel, { color: theme.text }]}>
                  Generar reporte
                </Text>
              </Pressable>
            </View>

            <View style={{ height: 8 }} />

            <View style={styles.section}>
              <Pressable
                onPress={handleLogout}
                style={({ pressed }) => [
                  styles.logoutRow,
                  {
                    backgroundColor: pressed ? "#2b2b2b" : "#dc3545",
                    ...createShadow(0, 4, 8, theme.shadow, 4),
                  },
                ]}
              >
                <Text style={[styles.logoutText]}>Cerrar sesión</Text>
              </Pressable>
            </View>

            <View style={{ height: 40 }} />
          </ScrollView>
        </Animated.View>
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  container: {
    padding: 20,
    paddingBottom: 40,
    paddingTop: 20,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 18,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: "800",
  },
  headerSubtitle: {
    marginTop: 4,
    fontSize: 13,
  },
  closeButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.12)", 6),
  },
  featuredWrapper: {
    borderRadius: 18,
    marginBottom: 18,
  },
  featuredCard: {
    borderRadius: 18,
    padding: 18,
  },
  featuredContent: {
    flexDirection: "row",
    alignItems: "center",
  },
  featuredTitle: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "800",
    marginBottom: 4,
  },
  featuredSubtitle: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 13,
    lineHeight: 18,
  },
  featuredBadge: {
    marginTop: 12,
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  featuredBadgeText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 12,
    letterSpacing: 0.4,
  },
  featuredIcon: {
    width: 56,
    height: 56,
    borderRadius: 16,
    backgroundColor: "rgba(255,255,255,0.18)",
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 16,
  },
  section: {
    marginBottom: 12,
  },
  menuRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    marginBottom: 10,
    borderWidth: 1,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  menuLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  iconBox: {
    width: 46,
    height: 46,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  menuSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  menuRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  notificationBadge: {
    backgroundColor: "#ff6b6b",
    borderRadius: 12,
    minWidth: 24,
    height: 24,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 6,
  },
  notificationBadgeText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
  actionButton: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 12,
    marginBottom: 10,
    borderWidth: 1,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  actionLabel: {
    marginLeft: 10,
    fontSize: 15,
    fontWeight: "700",
  },
  logoutRow: {
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  logoutText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: 15,
  },
});
