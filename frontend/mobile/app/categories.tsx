import { useState, useEffect } from "react";
import { View, StyleSheet, FlatList, Pressable, Text } from "react-native";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { getCategories } from "shared";

// Colores predefinidos para categorías
const CATEGORY_COLORS = [
  "#ff6b6b",
  "#4dd0e1",
  "#8bc34a",
  "#ffb86b",
  "#7c4dff",
  "#e91e63",
  "#00bcd4",
  "#4caf50",
  "#ff9800",
  "#9c27b0",
  "#f44336",
  "#03a9f4",
  "#cddc39",
  "#ff5722",
  "#673ab7",
];

// Emojis por nombre de categoría (mapeo común)
const CATEGORY_EMOJIS: Record<string, string> = {
  alimentación: "🍕",
  comida: "🍕",
  food: "🍕",
  transporte: "🚗",
  transport: "🚗",
  hogar: "🏠",
  home: "🏠",
  entretenimiento: "🎬",
  entertainment: "🎬",
  salud: "💊",
  health: "💊",
  educación: "📚",
  education: "📚",
  compras: "🛒",
  shopping: "🛒",
  servicios: "🔧",
  services: "🔧",
  otros: "📦",
  other: "📦",
  general: "📦",
};

type Category = {
  id: number;
  name: string;
  description?: string | null;
  is_default: boolean;
  user_id?: number | null;
  updated_at: string;
  created_at: string;
};

export default function CategoriesScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    getCategories().then((data) => setCategories(data));
  }, []);

  // Obtener color para una categoría basado en su índice
  const getCategoryColor = (index: number) => {
    return CATEGORY_COLORS[index % CATEGORY_COLORS.length];
  };

  // Obtener emoji para una categoría basado en su nombre
  const getCategoryEmoji = (name: string) => {
    const lowerName = name.toLowerCase();
    return CATEGORY_EMOJIS[lowerName] || "🏷️";
  };

  const renderItem = ({ item, index }: { item: Category; index: number }) => {
    const color = getCategoryColor(index);
    const emoji = getCategoryEmoji(item.name);

    return (
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
          <View style={[styles.iconWrap, { backgroundColor: color + "22" }]}>
            <Text style={{ fontSize: 18 }}>{emoji}</Text>
          </View>
          <View style={{ marginLeft: 12, flex: 1 }}>
            <ThemedText
              style={[styles.title, { color: theme.text }]}
              numberOfLines={1}
            >
              {item.name}
            </ThemedText>
            <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
              {item.description ||
                (item.is_default
                  ? "Categoría predeterminada"
                  : "Categoría personalizada")}
            </ThemedText>
          </View>
        </View>

        <View style={styles.right}>
          <View style={[styles.badge, { backgroundColor: color + "22" }]}>
            <Text style={{ color: color, fontSize: 12, fontWeight: "600" }}>
              {item.is_default ? "Default" : "Custom"}
            </Text>
          </View>
        </View>
      </Pressable>
    );
  };

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
        keyExtractor={(c) => c.id.toString()}
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
            backgroundColor: theme.tint,
            ...createShadow(0, 6, 8, theme.shadow, 8),
          },
        ]}
      >
        <IconSymbol
          name={"plus" as any}
          size={20}
          color={isDark ? "#1a1a1a" : "#fff"}
        />
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
    alignItems: "flex-end",
    marginLeft: 12,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
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
