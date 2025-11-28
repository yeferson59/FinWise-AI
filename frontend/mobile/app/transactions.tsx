import { useState, useEffect } from "react";
import { View, FlatList, StyleSheet, Pressable, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import { getTransactions } from "shared";

type Transaction = {
  id: string;
  user_id: number;
  category_id: number;
  source_id: number;
  title?: string;
  description: string;
  amount: number;
  date: string;
  state: string;
  updated_at: string;
  created_at: string;
};

export default function TransactionsScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    if (user?.id) {
      getTransactions(user.id, 0, 50).then((data) => setTransactions(data));
    }
  }, [user?.id]);

  const onPressTransaction = (id: string) => {
    // navigate to detail (placeholder route)
    // TODO: implement nested routes or detail screen
  };

  const renderItem = ({ item }: { item: Transaction }) => {
    const isPositive = item.amount >= 0;
    const amountColor = isPositive ? "#2dd4bf" : "#ff6b6b";
    const formattedDate = item.date
      ? new Date(item.date).toLocaleDateString("es-ES", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : "";

    return (
      <Pressable
        onPress={() => onPressTransaction(item.id)}
        style={({ pressed }) => [
          styles.row,
          {
            backgroundColor: pressed
              ? isDark
                ? "#222"
                : "#f5f7fb"
              : theme.cardBackground,
            ...createShadow(0, 4, 8, theme.shadow, 3),
          },
        ]}
      >
        <View style={styles.left}>
          <View
            style={[
              styles.iconWrap,
              { backgroundColor: isDark ? "rgba(255,255,255,0.03)" : "#fff" },
            ]}
          >
            <IconSymbol
              name={
                isPositive
                  ? ("arrow.down.circle" as any)
                  : ("arrow.up.circle" as any)
              }
              size={18}
              color={amountColor}
            />
          </View>
          <View style={{ marginLeft: 12, flex: 1 }}>
            <Text
              style={[styles.title, { color: theme.text }]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              {item.title || item.description || "Sin descripción"}
            </Text>
            <Text style={[styles.subtitle, { color: theme.icon }]}>
              {item.state === "pending" ? "Pendiente" : "Completada"}
            </Text>
          </View>
        </View>

        <View style={styles.right}>
          <Text style={[styles.dateText, { color: theme.icon }]}>
            {formattedDate}
          </Text>
          <Text style={[styles.amountText, { color: amountColor }]}>
            {isPositive ? "+" : "-"}${Math.abs(item.amount).toFixed(2)}
          </Text>
        </View>
      </Pressable>
    );
  };

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <SafeAreaView style={{ padding: 20 }}>
        <ThemedText type="title" style={[styles.header, { color: theme.text }]}>
          Transacciones
        </ThemedText>
        <ThemedText style={[styles.headerSub, { color: theme.icon }]}>
          Últimos movimientos
        </ThemedText>

        <FlatList
          data={transactions}
          keyExtractor={(t) => t.id}
          renderItem={renderItem}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          contentContainerStyle={{ paddingTop: 16, paddingBottom: 60 }}
          showsVerticalScrollIndicator={false}
        />

        <Pressable
          onPress={() => {}}
          style={({ pressed }) => [
            styles.addButton,
            { backgroundColor: pressed ? "#0b7285" : theme.tint },
          ]}
        >
          <IconSymbol
            name={"plus" as any}
            size={20}
            color={isDark ? "#1a1a1a" : "#fff"}
          />
          <ThemedText
            style={{ color: isDark ? "#1a1a1a" : "#fff", marginLeft: 8 }}
          >
            Nueva
          </ThemedText>
        </Pressable>
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    fontSize: 26,
    fontWeight: "800",
    marginBottom: 2,
  },
  headerSub: {
    fontSize: 13,
    marginBottom: 12,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 3),
    justifyContent: "space-between",
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    marginRight: 12,
  },
  iconWrap: {
    width: 46,
    height: 46,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 13,
    marginTop: 4,
  },
  right: {
    alignItems: "flex-end",
    marginLeft: 12,
    width: 110,
  },
  dateText: {
    fontSize: 12,
  },
  amountText: {
    fontSize: 16,
    fontWeight: "800",
    marginTop: 6,
  },
  addButton: {
    position: "absolute",
    right: 28,
    bottom: 24,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.18)", 6),
  },
});
