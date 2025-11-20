import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { Platform } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import "react-native-reanimated";

export const unstable_settings = {
  anchor: "index",
};

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
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
          <Stack.Screen name="transactions" />
          <Stack.Screen name="categories" />
          <Stack.Screen name="reports" />
          <Stack.Screen name="budget" />
          <Stack.Screen name="integrations" />
          <Stack.Screen name="notifications" />
          <Stack.Screen name="settings" />
        </Stack>
        <StatusBar style="auto" />
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}
