import React, { useMemo } from "react";
import {
  View,
  StyleSheet,
  FlatList,
  Pressable,
  Text,
  Dimensions,
} from "react-native";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

type Category = {
  id: string;
  name: string;
  amount: number;
  percent: number;
  color: string;
  emoji?: string;
};

export default function CategoriesScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const categories = useMemo<Category[]>(
    () => [
      {
        id: "1",
        name: "Alimentación",
        amount: 450,
        percent: 35,
        color: "#ff6b6b",
        emoji: "🍕",
      },
      {
        id: "2",
        name: "Transporte",
        amount: 280,
        percent: 22,
        color: "#4dd0e1",
        emoji: "🚗",
      },
      {
        id: "3",
        name: "Hogar",
        amount: 380,
        percent: 30,
        color: "#8bc34a",
        emoji: "🏠",
      },
      {
        id: "4",
        name: "Entretenimiento",
        amount: 120,
        percent: 8,
        color: "#ffb86b",
        emoji: "🎬",
      },
      {
        id: "5",
        name: "Salud",
        amount: 90,
        percent: 5,
        color: "#7c4dff",
        emoji: "💊",
      },
    ],
    [],
  );

  const renderItem = ({ item }: { item: Category }) => (
    <Pressable
      style={[
        styles.row,
        {
          backgroundColor: theme.cardBackground,
          ...createShadow(0, 6, 8, theme.shadow, 4),
        },
      ]}
      onPress={() => {}}
    >
      <View style={styles.left}>
        <View style={[styles.iconWrap, { backgroundColor: item.color + "22" }]}>
          <Text style={{ fontSize: 18 }}>{item.emoji ?? "🏷️"}</Text>
        </View>
        <View style={{ marginLeft: 12 }}>
          <ThemedText style={[styles.title, { color: theme.text }]}>
            {item.name}
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            ${item.amount.toFixed(2)}
          </ThemedText>
        </View>
      </View>

      <View style={styles.right}>
        <View
          style={[
            styles.progressBg,
            { backgroundColor: isDark ? "#2b2b2b" : "#eef2f5" },
          ]}
        >
          <View
            style={[
              styles.progressFill,
              { width: `${item.percent}%`, backgroundColor: item.color },
            ]}
          />
        </View>
        <ThemedText style={[styles.percent, { color: theme.icon }]}>
          {item.percent}%
        </ThemedText>
      </View>
    </Pressable>
  );

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.header}>
        <ThemedText
          type="title"
          style={[styles.headerTitle, { color: theme.text }]}
        >
          Categorías
        </ThemedText>
        <ThemedText style={[styles.headerSubtitle, { color: theme.icon }]}>
          Administra y revisa tus categorías
        </ThemedText>
      </View>

      <FlatList
        data={categories}
        keyExtractor={(c) => c.id}
        contentContainerStyle={{ padding: 20, paddingBottom: 48 }}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        showsVerticalScrollIndicator={false}
      />

      <Pressable
        onPress={() => {}}
        style={[
          styles.fab,
          {
            backgroundColor: "#007bff",
            ...createShadow(0, 6, 8, theme.shadow, 8),
          },
        ]}
      >
        <IconSymbol name={"plus" as any} size={20} color={"#fff"} />
      </Pressable>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: "800",
  },
  headerSubtitle: {
    fontSize: 13,
    marginTop: 6,
  },
  row: {
    padding: 14,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.06)", 4),
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  right: {
    width: Math.min(120, SCREEN_WIDTH * 0.35),
    alignItems: "flex-end",
    marginLeft: 12,
  },
  progressBg: {
    width: "100%",
    height: 8,
    borderRadius: 999,
    overflow: "hidden",
    marginBottom: 8,
  },
  progressFill: {
    height: "100%",
    borderRadius: 999,
  },
  percent: {
    fontSize: 12,
  },
  fab: {
    position: "absolute",
    right: 18,
    bottom: 26,
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.18)", 8),
  },
});
