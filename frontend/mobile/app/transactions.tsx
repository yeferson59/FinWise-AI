import React, { useMemo } from "react";
import { View, FlatList, StyleSheet, Pressable, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

type Transaction = {
  id: string;
  title: string;
  category: string;
  amount: number;
  date: string;
  type: "expense" | "income";
  icon?: string;
};

export default function TransactionsScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const transactions: Transaction[] = useMemo(
    () => [
      {
        id: "t1",
        title: "Compra Supermercado",
        category: "Alimentación",
        amount: 72.5,
        date: "2025-11-10",
        type: "expense",
        icon: "pizza",
      },
      {
        id: "t2",
        title: "Sueldo",
        category: "Ingresos",
        amount: 2500,
        date: "2025-11-01",
        type: "income",
        icon: "dollarsign.circle",
      },
      {
        id: "t3",
        title: "Taxi",
        category: "Transporte",
        amount: 12.75,
        date: "2025-11-12",
        type: "expense",
        icon: "car",
      },
      {
        id: "t4",
        title: "Pago Electricidad",
        category: "Hogar",
        amount: 55.0,
        date: "2025-11-07",
        type: "expense",
        icon: "home",
      },
    ],
    [],
  );

  const onPressTransaction = (id: string) => {
    // navigate to detail (placeholder route)
    // TODO: implement nested routes or detail screen
  };

  const renderItem = ({ item }: { item: Transaction }) => {
    const amountColor = item.type === "income" ? "#2dd4bf" : "#ff6b6b";
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
              name={(item.icon as any) ?? ("tag" as any)}
              size={18}
              color={theme.tint}
            />
          </View>
          <View style={{ marginLeft: 12 }}>
            <Text
              style={[styles.title, { color: theme.text }]}
              numberOfLines={1}
            >
              {item.title}
            </Text>
            <Text style={[styles.subtitle, { color: theme.icon }]}>
              {item.category}
            </Text>
          </View>
        </View>

        <View style={styles.right}>
          <Text style={[styles.dateText, { color: theme.icon }]}>
            {item.date}
          </Text>
          <Text style={[styles.amountText, { color: amountColor }]}>
            {item.type === "income" ? "+" : "-"}${item.amount.toFixed(2)}
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
          <IconSymbol name={"plus" as any} size={20} color={"#fff"} />
          <ThemedText style={{ color: "#fff", marginLeft: 8 }}>
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
    maxWidth: 220,
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
