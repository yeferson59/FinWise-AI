import React from "react";
import { View, StyleSheet, Pressable, Switch } from "react-native";
import { useRouter } from "expo-router";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

export default function IntegrationsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];

  // Example local state for toggles (placeholder UI)
  const [connected, setConnected] = React.useState({
    bankA: false,
    bankB: true,
    plaid: false,
  });

  return (
    <ThemedView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <ThemedText type="title" style={[styles.title, { color: theme.text }]}>
          Integraciones
        </ThemedText>
        <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
          Conecta bancos y servicios para importar transacciones
        </ThemedText>
      </View>

      <View style={[styles.card, { backgroundColor: theme.cardBackground, shadowColor: theme.shadow }]}>
        <View style={styles.row}>
          <View style={styles.rowLeft}>
            <IconSymbol name={"link" as any} size={22} color={theme.tint} />
            <ThemedText style={[styles.itemTitle, { color: theme.text }]}>Bancos</ThemedText>
          </View>
          <Pressable onPress={() => {}} style={styles.action}>
            <ThemedText style={{ color: theme.tint, fontWeight: "700" }}>Conectar</ThemedText>
          </Pressable>
        </View>

        <View style={styles.integrationList}>
          <View style={styles.integrationRow}>
            <View style={styles.integrationLeft}>
              <IconSymbol name={"home" as any} size={20} color={theme.tint} />
              <ThemedText style={[styles.integrationName, { color: theme.text }]}>Banco A</ThemedText>
            </View>
            <Switch
              value={connected.bankA}
              onValueChange={(v) => setConnected((s) => ({ ...s, bankA: v }))}
              trackColor={{ true: theme.secondary, false: "#ccc" }}
              thumbColor={connected.bankA ? "#fff" : "#fff"}
            />
          </View>

          <View style={styles.integrationRow}>
            <View style={styles.integrationLeft}>
              <IconSymbol name={"car" as any} size={20} color={theme.tint} />
              <ThemedText style={[styles.integrationName, { color: theme.text }]}>Banco B</ThemedText>
            </View>
            <Switch
              value={connected.bankB}
              onValueChange={(v) => setConnected((s) => ({ ...s, bankB: v }))}
              trackColor={{ true: theme.secondary, false: "#ccc" }}
              thumbColor={connected.bankB ? "#fff" : "#fff"}
            />
          </View>

          <View style={styles.integrationRow}>
            <View style={styles.integrationLeft}>
              <IconSymbol name={"sparkles" as any} size={20} color={theme.tint} />
              <ThemedText style={[styles.integrationName, { color: theme.text }]}>Plaid (demo)</ThemedText>
            </View>
            <Switch
              value={connected.plaid}
              onValueChange={(v) => setConnected((s) => ({ ...s, plaid: v }))}
              trackColor={{ true: theme.secondary, false: "#ccc" }}
              thumbColor={connected.plaid ? "#fff" : "#fff"}
            />
          </View>
        </View>
      </View>

      <View style={styles.footer}>
        <Pressable onPress={() => router.back()} style={[styles.backButton, { backgroundColor: theme.tint }]}>
          <ThemedText style={{ color: "#fff", fontWeight: "700" }}>Volver</ThemedText>
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
    padding: 20,
    paddingBottom: 8,
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
    padding: 14,
    borderRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 6,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  rowLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  action: {
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  itemTitle: {
    marginLeft: 10,
    fontSize: 16,
    fontWeight: "700",
  },
  integrationList: {
    marginTop: 14,
  },
  integrationRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "rgba(0,0,0,0.06)",
  },
  integrationLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  integrationName: {
    marginLeft: 10,
    fontSize: 15,
    fontWeight: "700",
  },
  footer: {
    padding: 20,
    paddingTop: 6,
  },
  backButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
});
