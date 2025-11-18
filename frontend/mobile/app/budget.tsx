import React from "react";
import { View, StyleSheet, Pressable, FlatList, Platform } from "react-native";
import { useRouter } from "expo-router";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { IconSymbol } from "@/components/ui/icon-symbol";

type Budget = {
  id: string;
  name: string;
  limit: string;
  spent: string;
  percent: number;
  color: string;
};

const MOCK_BUDGETS: Budget[] = [
  {
    id: "1",
    name: "Alimentación",
    limit: "$600.00",
    spent: "$450.00",
    percent: 75,
    color: "#ff6b6b",
  },
  {
    id: "2",
    name: "Transporte",
    limit: "$350.00",
    spent: "$280.00",
    percent: 80,
    color: "#4dd0e1",
  },
  {
    id: "3",
    name: "Ocio",
    limit: "$200.00",
    spent: "$120.00",
    percent: 60,
    color: "#ffb86b",
  },
];

export default function BudgetScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const renderItem = ({ item }: { item: Budget }) => {
    return (
      <View
        style={[
          styles.card,
          {
            backgroundColor: theme.cardBackground,
            ...createShadow(0, 6, 8, theme.shadow, 4),
          },
        ]}
      >
        <View style={styles.cardLeft}>
          <View
            style={[styles.iconBox, { backgroundColor: item.color + "22" }]}
          >
            <IconSymbol name={"wallet" as any} size={18} color={item.color} />
          </View>
          <View style={{ marginLeft: 12 }}>
            <ThemedText style={[styles.cardTitle, { color: theme.text }]}>
              {item.name}
            </ThemedText>
            <ThemedText style={{ color: theme.icon }}>
              {item.spent} / {item.limit}
            </ThemedText>
          </View>
        </View>

        <View style={styles.cardRight}>
          <View
            style={[
              styles.progressBg,
              { backgroundColor: isDark ? "#2a2a2a" : "#eef2f5" },
            ]}
          >
            <View
              style={[
                styles.progressFill,
                { width: `${item.percent}%`, backgroundColor: item.color },
              ]}
            />
          </View>
          <ThemedText style={{ color: theme.icon }}>{item.percent}%</ThemedText>
        </View>
      </View>
    );
  };

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.header}>
        <View>
          <ThemedText
            type="title"
            style={[styles.title, { color: theme.text }]}
          >
            Presupuestos
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            Crea y administra tus presupuestos mensuales
          </ThemedText>
        </View>

        <Pressable
          onPress={() => router.back()}
          style={[
            styles.headerButton,
            {
              backgroundColor: theme.cardBackground,
              ...createShadow(0, 4, 8, theme.shadow, 6),
            },
          ]}
        >
          <IconSymbol
            name={Platform.OS === "ios" ? ("xmark" as any) : ("close" as any)}
            size={18}
            color={theme.icon}
          />
        </Pressable>
      </View>

      <View style={styles.actionsRow}>
        <Pressable
          style={[
            styles.action,
            { backgroundColor: isDark ? "#121212" : "#f2fbff" },
          ]}
          onPress={() => {}}
        >
          <IconSymbol name={"plus" as any} size={20} color={theme.tint} />
          <ThemedText style={[styles.actionLabel, { color: theme.text }]}>
            Nuevo presupuesto
          </ThemedText>
        </Pressable>

        <Pressable
          style={[
            styles.action,
            { backgroundColor: isDark ? "#121212" : "#fff0fb" },
          ]}
          onPress={() => router.push("/reports")}
        >
          <IconSymbol name={"document" as any} size={20} color={theme.tint} />
          <ThemedText style={[styles.actionLabel, { color: theme.text }]}>
            Exportar
          </ThemedText>
        </Pressable>
      </View>

      <View style={styles.sectionHeader}>
        <ThemedText style={[styles.sectionTitle, { color: theme.text }]}>
          Tus presupuestos
        </ThemedText>
        <ThemedText style={[styles.sectionSubtitle, { color: theme.icon }]}>
          {MOCK_BUDGETS.length} activos
        </ThemedText>
      </View>

      <FlatList
        data={MOCK_BUDGETS}
        keyExtractor={(i) => i.id}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 20, paddingBottom: 80 }}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
      />
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
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.12)", 6),
  },
  title: {
    fontSize: 24,
    fontWeight: "800",
  },
  subtitle: {
    marginTop: 4,
    fontSize: 13,
  },
  actionsRow: {
    flexDirection: "row",
    paddingHorizontal: 20,
    justifyContent: "space-between",
    marginTop: 8,
  },
  action: {
    flex: 1,
    marginHorizontal: 6,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  actionLabel: {
    marginTop: 6,
    fontSize: 13,
  },
  sectionHeader: {
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 6,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  sectionSubtitle: {
    fontSize: 13,
    fontWeight: "600",
  },
  card: {
    padding: 14,
    borderRadius: 12,
    marginHorizontal: 20,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.06)", 4),
  },
  cardLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  iconBox: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  cardRight: {
    width: 120,
    alignItems: "flex-end",
  },
  progressBg: {
    width: "100%",
    height: 8,
    borderRadius: 999,
    overflow: "hidden",
    marginBottom: 6,
  },
  progressFill: {
    height: "100%",
    borderRadius: 999,
  },
});
