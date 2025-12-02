import { Stack, useRouter } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { Platform, Pressable, StyleSheet, View } from "react-native";
import { SafeAreaProvider, useSafeAreaInsets } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { AuthProvider } from "@/contexts/AuthContext";
import { NotificationProvider } from "@/contexts/NotificationContext";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import "react-native-reanimated";

export const unstable_settings = {
  anchor: "index",
};

const GlobalMenuButton = () => {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const insets = useSafeAreaInsets();

  return (
    <View pointerEvents="box-none" style={styles.overlayContainer}>
      <Pressable
        accessibilityLabel="Abrir menú"
        onPress={() => router.push("/menu")}
        style={[
          styles.menuButton,
          {
            top: insets.top + 12,
            backgroundColor: isDark ? "#262626" : theme.cardBackground,
            borderColor: isDark ? "rgba(255,255,255,0.08)" : "transparent",
            ...createShadow(0, 4, 8, isDark ? "rgba(0,0,0,0.6)" : theme.shadow, 8),
          },
        ]}
      >
        <IconSymbol name={"line.3.horizontal" as any} size={20} color={theme.tint} />
      </Pressable>
    </View>
  );
};

const LayoutContainer = () => {
  const insets = useSafeAreaInsets();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const topSpacing = Math.max(insets.top, 20) + 12;

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: theme.background }}>
      <View style={{ flex: 1, backgroundColor: theme.background }}>
        <View style={{ flex: 1, paddingTop: topSpacing, backgroundColor: theme.background }}>
          <Stack screenOptions={{ headerShown: false }}>
            <Stack.Screen name="index" />
            <Stack.Screen name="login" />
            <Stack.Screen name="register" />
            <Stack.Screen name="home" />
            <Stack.Screen
              name="menu"
              options={{
                presentation: Platform.OS === "web" ? "card" : "modal",
              }}
            />
            <Stack.Screen name="profile" />
            <Stack.Screen name="assistant" />
            <Stack.Screen name="ocr" />
            <Stack.Screen name="audio-transaction" />
            <Stack.Screen name="transactions" />
            <Stack.Screen
              name="transaction-detail"
              options={{
                presentation: Platform.OS === "web" ? "card" : "modal",
              }}
            />
            <Stack.Screen name="categories" />
            <Stack.Screen name="reports" />
            <Stack.Screen name="report-detail" />
            <Stack.Screen name="budget" />
            <Stack.Screen name="integrations" />
            <Stack.Screen name="notifications" />
            <Stack.Screen name="settings" />
          </Stack>
        </View>
        <GlobalMenuButton />
      </View>
      <StatusBar style="auto" />
    </GestureHandlerRootView>
  );
};

export default function RootLayout() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <SafeAreaProvider>
          <LayoutContainer />
        </SafeAreaProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  overlayContainer: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: "box-none",
    alignItems: "flex-end",
  },
  menuButton: {
    position: "absolute",
    right: 16,
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
});
