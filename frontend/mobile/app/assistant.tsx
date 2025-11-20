import React from "react";
import { View, StyleSheet, Pressable } from "react-native";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

/**
 * Assistant placeholder screen
 * - Minimal placeholder to integrate into navigation
 * - Uses app theming for consistent appearance
 */

export default function AssistantScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.header}>
        <IconSymbol
          name={isDark ? ("sparkles" as any) : ("sparkles" as any)}
          size={44}
          color={theme.tint}
        />
        <ThemedText type="title" style={[styles.title, { color: theme.text }]}>
          Asistente IA
        </ThemedText>
        <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
          Un asistente inteligente para ayudarte a entender tus finanzas
        </ThemedText>
      </View>

      <View
        style={[
          styles.card,
          {
            backgroundColor: theme.cardBackground,
            ...createShadow(0, 6, 10, theme.shadow, 8),
          },
        ]}
      >
        <ThemedText style={[styles.cardText, { color: theme.icon }]}>
          Aquí estará el asistente conversacional. Por ahora este es un
          placeholder que sirve para integrar la navegación y el tema con el
          resto de la aplicación.
        </ThemedText>

        <Pressable
          onPress={() => {}}
          style={({ pressed }) => [
            styles.button,
            {
              backgroundColor: pressed
                ? isDark
                  ? "#0f5132"
                  : "#e6f9f0"
                : theme.secondary,
            },
          ]}
        >
          <ThemedText style={[styles.buttonText, { color: "#fff" }]}>
            Ir al chat del asistente
          </ThemedText>
        </Pressable>

        <Pressable
          onPress={() => router.back()}
          style={({ pressed }) => [
            styles.ghostButton,
            {
              borderColor: pressed ? theme.tint : "transparent",
            },
          ]}
        >
          <ThemedText style={[styles.ghostText, { color: theme.icon }]}>
            Volver
          </ThemedText>
        </Pressable>
      </View>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 28,
    paddingBottom: 18,
    alignItems: "flex-start",
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
    marginTop: 8,
  },
  subtitle: {
    fontSize: 13,
    marginTop: 6,
  },
  card: {
    margin: 20,
    padding: 18,
    borderRadius: 14,
  },
  cardText: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 18,
  },
  button: {
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
    marginBottom: 12,
  },
  buttonText: {
    fontWeight: "700",
    fontSize: 15,
  },
  ghostButton: {
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
    borderWidth: 1,
  },
  ghostText: {
    fontSize: 14,
    fontWeight: "700",
  },
});
