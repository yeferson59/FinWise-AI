import React from "react";
import {
  View,
  StyleSheet,
  Pressable,
  Alert,
  Platform,
} from "react-native";
import { useRouter } from "expo-router";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

/**
 * OCR placeholder screen
 * - Placeholder UI for scanning/processing documents (receipts, invoices)
 * - Appears in the app menu as /ocr
 * - Replace the `onStartScan` handler with real OCR integration later
 */

export default function OcrScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const onStartScan = () => {
    // Placeholder: show a friendly alert
    Alert.alert(
      "OCR (placeholder)",
      "Aquí se integrará el escaneo y reconocimiento de documentos.\n\nReemplaza esta función con la integración de OCR (Tesseract / EasyOCR / DocTR) y el endpoint del backend.",
      [{ text: "Entendido" }],
    );
  };

  return (
    <ThemedView style={[styles.root, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <ThemedText type="title" style={[styles.title, { color: theme.text }]}>
          OCR - Escanear documentos
        </ThemedText>
        <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
          Escanea recibos, facturas y documentos. (Placeholder)
        </ThemedText>
      </View>

      <View
        style={[
          styles.card,
          {
            backgroundColor: isDark ? "#222" : theme.cardBackground,
            shadowColor: theme.shadow,
          },
        ]}
      >
        <IconSymbol
          name={Platform.OS === "ios" ? ("doc.text.viewfinder" as any) : ("document" as any)}
          size={48}
          color={theme.tint}
        />
        <ThemedText style={[styles.cardTitle, { color: theme.text }]}>
          Escaneo rápido
        </ThemedText>
        <ThemedText style={[styles.cardText, { color: theme.icon }]}>
          Usa la cámara para capturar recibos y extraer datos automáticamente.
        </ThemedText>

        <View style={styles.actions}>
          <Pressable
            onPress={onStartScan}
            style={({ pressed }) => [
              styles.scanButton,
              { backgroundColor: pressed ? theme.inputBackground : theme.tint },
            ]}
          >
            <ThemedText style={styles.scanText}>Iniciar escaneo</ThemedText>
          </Pressable>

          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [
              styles.backButton,
              { borderColor: pressed ? theme.inputBackground : theme.tint },
            ]}
          >
            <ThemedText style={[styles.backText, { color: theme.tint }]}>
              Volver
            </ThemedText>
          </Pressable>
        </View>
      </View>

      <View style={styles.note}>
        <ThemedText style={{ color: theme.icon, fontSize: 13 }}>
          - Esta pantalla es un placeholder. Integra el flujo de cámara y el
          endpoint OCR del backend para procesar documentos automáticamente.
        </ThemedText>
      </View>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 28,
    paddingBottom: 10,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
  },
  subtitle: {
    marginTop: 6,
    fontSize: 13,
  },
  card: {
    margin: 20,
    borderRadius: 14,
    padding: 20,
    alignItems: "center",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 8,
  },
  cardTitle: {
    marginTop: 12,
    fontSize: 18,
    fontWeight: "700",
  },
  cardText: {
    marginTop: 6,
    fontSize: 14,
    textAlign: "center",
    maxWidth: 320,
  },
  actions: {
    marginTop: 18,
    width: "100%",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  scanButton: {
    flex: 1,
    marginRight: 8,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  scanText: {
    color: "#fff",
    fontWeight: "700",
  },
  backButton: {
    flex: 1,
    marginLeft: 8,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  backText: {
    fontWeight: "700",
  },
  note: {
    paddingHorizontal: 20,
    marginTop: 12,
  },
});
