import { useMemo, useState, useEffect } from "react";
import {
  View,
  TouchableOpacity,
  StyleSheet,
  Text,
  Pressable,
  FlatList,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import {
  useSafeAreaInsets,
  SafeAreaView,
} from "react-native-safe-area-context";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import { getTransactions, getCategories, getSources } from "shared";

type CategoryExpense = {
  id: string;
  name: string;
  amount: string;
  percent: number;
  color: string;
  emoji?: string;
};

type BackendCategory = {
  id: number;
  name: string;
  description?: string | null;
  is_default: boolean;
  user_id?: number | null;
  updated_at: string;
  created_at: string;
};

type BackendSource = {
  id: number;
  name: string;
};

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
];

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

export default function HomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();
  const [range, setRange] = useState<"Día" | "Semana" | "Mes" | "Año">("Mes");
  const [recentTransactions, setRecentTransactions] = useState<
    {
      id: string;
      user_id: number;
      category_id: number;
      source_id: number;
      title?: string;
      description: string;
      amount: number;
      transaction_type: "income" | "expense";
      date: string;
      state: string;
      updated_at: string;
      created_at: string;
    }[]
  >([]);
  const [backendCategories, setBackendCategories] = useState<BackendCategory[]>([]);
  const [backendSources, setBackendSources] = useState<BackendSource[]>([]);

  useEffect(() => {
    if (user?.id) {
      getTransactions(user.id).then((data) => setRecentTransactions(data));
      getCategories().then((data) => setBackendCategories(data));
      getSources().then((data) => setBackendSources(data));
    }
  }, [user?.id]);

  const getCategoryName = (id: number) => {
    const cat = backendCategories.find((c) => c.id === id);
    return cat?.name || "Sin categoría";
  };

  const getSourceName = (id: number) => {
    const src = backendSources.find((s) => s.id === id);
    return src?.name || "Sin fuente";
  };

  const categoryExpenses: CategoryExpense[] = useMemo(() => {
    if (backendCategories.length === 0 || recentTransactions.length === 0) {
      return [];
    }

    // Calculate expenses per category (only expense transactions)
    const expensesByCategory: Record<number, number> = {};
    recentTransactions.forEach((tx) => {
      if (tx.transaction_type === "expense") {
        const categoryId = tx.category_id;
        expensesByCategory[categoryId] = (expensesByCategory[categoryId] || 0) + tx.amount;
      }
    });

    const totalExpenses = Object.values(expensesByCategory).reduce((sum, val) => sum + val, 0);

    // Map backend categories to display format with calculated amounts
    return backendCategories
      .filter((cat) => expensesByCategory[cat.id] !== undefined)
      .map((cat, index) => {
        const amount = expensesByCategory[cat.id] || 0;
        const percent = totalExpenses > 0 ? Math.round((amount / totalExpenses) * 100) : 0;
        const lowerName = cat.name.toLowerCase();
        
        return {
          id: cat.id.toString(),
          name: cat.name,
          amount: `$${amount.toFixed(2)}`,
          percent,
          color: CATEGORY_COLORS[index % CATEGORY_COLORS.length],
          emoji: CATEGORY_EMOJIS[lowerName] || "🏷️",
        };
      })
      .sort((a, b) => b.percent - a.percent);
  }, [backendCategories, recentTransactions]);

  const budgetAlerts = useMemo(
    () => [
      {
        id: "b1",
        name: "Alimentación",
        percent: 85,
        color: "#ff6b6b",
        emoji: "🍕",
      },
      {
        id: "b2",
        name: "Transporte",
        percent: 92,
        color: "#4dd0e1",
        emoji: "🚗",
      },
    ],
    [],
  );

  const savingsGoals = useMemo(
    () => [
      {
        id: "s1",
        name: "Viaje a Miami",
        current: "$2,450",
        goal: "$5,000",
        percent: 49,
        color: "#8bc34a",
      },
    ],
    [],
  );

  if (!user) return null;

  const totalBalance = "$1,250.00";
  const ingresos = "$4,000";
  const gastos = "$2,750";
  const change = "+12.5%";

  const renderAction = (icon: string, label: string, idx: number) => (
    <Pressable
      key={idx}
      style={[
        styles.action,
        {
          backgroundColor: theme.inputBackground,
          ...createShadow(0, 4, 8, theme.shadow, 4),
        },
      ]}
      onPress={() => {}}
    >
      <View
        style={[
          styles.actionIcon,
          { backgroundColor: isDark ? "#062f24" : "#eef6f5" },
        ]}
      >
        <IconSymbol name={icon as any} size={20} color={theme.tint} />
      </View>
      <Text style={[styles.actionLabel, { color: theme.icon }]}>{label}</Text>
    </Pressable>
  );

  const onPressTransaction = (item: any) => {
    router.push({
      pathname: "/transaction-detail",
      params: {
        id: item.id,
        title: item.title || "",
        description: item.description,
        amount: item.amount.toString(),
        transaction_type: item.transaction_type,
        date: item.date,
        state: item.state,
        category_name: getCategoryName(item.category_id),
        source_name: getSourceName(item.source_id),
        category_id: item.category_id.toString(),
        source_id: item.source_id.toString(),
        created_at: item.created_at,
        updated_at: item.updated_at,
      },
    });
  };

  const renderRecentTransaction = ({ item }: { item: any }) => {
    // Determine transaction type from backend field
    const isIncome = item.transaction_type === "income";
    // Color based on transaction type
    const transactionColor = isIncome ? "#25d1b2" : "#ff6b6b";
    // Format date for display
    const formattedDate = item.date
      ? new Date(item.date).toLocaleDateString("es-ES", {
          day: "numeric",
          month: "short",
          hour: "2-digit",
          minute: "2-digit",
        })
      : "";

    return (
      <Pressable
        onPress={() => onPressTransaction(item)}
        style={[
          styles.transactionItem,
          {
            backgroundColor: theme.cardBackground,
            ...createShadow(0, 4, 8, theme.shadow, 4),
          },
        ]}
      >
        <View style={styles.transactionLeft}>
          <View
            style={[
              styles.transactionIcon,
              { backgroundColor: transactionColor + "22" },
            ]}
          >
            <IconSymbol
              name={
                isIncome
                  ? ("arrow.down.circle" as any)
                  : ("arrow.up.circle" as any)
              }
              size={16}
              color={transactionColor}
            />
          </View>
          <View style={{ marginLeft: 10, flex: 1 }}>
            <Text
              style={[styles.transactionTitle, { color: theme.text }]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              {item.title || item.description || "Sin descripción"}
            </Text>
            <Text style={[styles.transactionTime, { color: theme.icon }]}>
              {formattedDate}
            </Text>
          </View>
        </View>
        <Text style={[styles.transactionAmount, { color: transactionColor }]}>
          {isIncome ? "+" : "-"}${item.amount.toFixed(2)}
        </Text>
      </Pressable>
    );
  };

  const renderBudgetAlert = ({ item }: { item: any }) => (
    <View
      style={[
        styles.budgetAlert,
        {
          backgroundColor: theme.cardBackground,
          ...createShadow(0, 4, 8, theme.shadow, 4),
        },
      ]}
    >
      <View style={styles.budgetAlertLeft}>
        <Text style={styles.budgetAlertEmoji}>{item.emoji}</Text>
        <View style={{ marginLeft: 8 }}>
          <Text style={[styles.budgetAlertName, { color: theme.text }]}>
            {item.name}
          </Text>
          <Text style={[styles.budgetAlertPercent, { color: theme.icon }]}>
            {item.percent}% del límite
          </Text>
        </View>
      </View>
      <View
        style={[
          styles.budgetAlertBadge,
          { backgroundColor: item.color + "22" },
        ]}
      >
        <Text style={[styles.budgetAlertValue, { color: item.color }]}>⚠️</Text>
      </View>
    </View>
  );

  const renderSavingsGoal = ({ item }: { item: any }) => (
    <View
      style={[
        styles.savingsCard,
        {
          backgroundColor: theme.cardBackground,
          ...createShadow(0, 4, 8, theme.shadow, 4),
        },
      ]}
    >
      <View style={styles.savingsHeader}>
        <Text style={[styles.savingsName, { color: theme.text }]}>
          {item.name}
        </Text>
        <Text style={[styles.savingsAmount, { color: theme.icon }]}>
          {item.current} / {item.goal}
        </Text>
      </View>
      <View
        style={[
          styles.savingsProgressBg,
          { backgroundColor: isDark ? "#2a2a2a" : "#eef2f5" },
        ]}
      >
        <View
          style={[
            styles.savingsProgressFill,
            { width: `${item.percent}%`, backgroundColor: item.color },
          ]}
        />
      </View>
      <Text style={[styles.savingsPercent, { color: theme.icon }]}>
        {item.percent}% completado
      </Text>
    </View>
  );

  const renderCategory = ({ item }: { item: CategoryExpense }) => {
    return (
      <View
        style={[
          styles.categoryCard,
          {
            backgroundColor: theme.cardBackground,
            ...createShadow(0, 4, 8, theme.shadow, 4),
          },
        ]}
      >
        <View style={styles.categoryLeft}>
          <View
            style={[
              styles.categoryIcon,
              { backgroundColor: item.color + "33" },
            ]}
          >
            <Text style={{ fontSize: 18 }}>{item.emoji ?? "🏷️"}</Text>
          </View>
          <View style={{ marginLeft: 12 }}>
            <Text style={[styles.categoryTitle, { color: theme.text }]}>
              {item.name}
            </Text>
            <Text style={[styles.categoryAmount, { color: theme.icon }]}>
              {item.amount}
            </Text>
          </View>
        </View>
        <View style={styles.categoryRight}>
          <View
            style={[
              styles.progressBarBg,
              { backgroundColor: isDark ? "#111" : "#eef2f5" },
            ]}
          >
            <View
              style={[
                styles.progressBar,
                { width: `${item.percent}%`, backgroundColor: item.color },
              ]}
            />
          </View>
          <Text style={[styles.categoryPercent, { color: theme.icon }]}>
            {item.percent}%
          </Text>
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.inputBackground }]}
    >
      <ScrollView
        contentContainerStyle={{ padding: 20, paddingTop: insets.top + 10 }}
      >
        <View style={styles.topRow}>
          <View>
            <Text style={[styles.greeting, { color: theme.text }]}>
              Hola, {user.first_name} {user.last_name}
            </Text>
            <Text style={[styles.subGreeting, { color: theme.icon }]}>
              Bienvenido de vuelta
            </Text>
          </View>
          <TouchableOpacity
            style={[
              styles.menuButton,
              {
                // slightly darker surface for dark mode and a subtle border so it reads on dark backgrounds
                backgroundColor: isDark ? "#262626" : theme.cardBackground,
                ...createShadow(
                  0,
                  4,
                  8,
                  isDark ? "rgba(0,0,0,0.6)" : theme.shadow,
                  6,
                ),
                borderWidth: 1,
                borderColor: isDark ? "rgba(255,255,255,0.04)" : "transparent",
              },
            ]}
            onPress={() => router.push("/menu")}
          >
            <Text style={{ fontSize: 20, color: theme.tint }}>☰</Text>
          </TouchableOpacity>
        </View>

        <View
          style={[
            styles.balanceCard,
            {
              // give cards a slightly different background in dark mode for better contrast
              backgroundColor: isDark ? "#222" : theme.cardBackground,
              // stronger shadow in dark to provide separation from the background
              ...createShadow(
                0,
                6,
                14,
                isDark ? "rgba(0,0,0,0.7)" : theme.shadow,
                12,
              ),
            },
          ]}
        >
          <View style={styles.balanceHeader}>
            <Text style={[styles.balanceLabel, { color: theme.icon }]}>
              BALANCE TOTAL
            </Text>
            <View
              style={[
                styles.changePill,
                { backgroundColor: isDark ? "#023a31" : "#e6faf3" },
              ]}
            >
              <Text
                style={{
                  color: isDark ? "#7af0c9" : "#0f5132",
                  fontWeight: "700",
                }}
              >
                {change}
              </Text>
            </View>
          </View>

          <Text style={[styles.balanceAmount, { color: theme.text }]}>
            {totalBalance}
          </Text>

          <View style={styles.balanceDivider} />

          <View style={styles.totalsRow}>
            <View style={styles.totalsItem}>
              <IconSymbol
                name={"arrow.down.circle.fill" as any}
                size={18}
                color="#25d1b2"
              />
              <View style={{ marginLeft: 8 }}>
                <Text style={[styles.totalsLabel, { color: theme.icon }]}>
                  Ingresos
                </Text>
                <Text style={[styles.totalsValue, { color: theme.text }]}>
                  {ingresos}
                </Text>
              </View>
            </View>
            <View style={[styles.totalsItem, { alignItems: "flex-end" }]}>
              <IconSymbol
                name={"arrow.up.circle.fill" as any}
                size={18}
                color="#ff6b6b"
              />
              <View style={{ marginLeft: 8, alignItems: "flex-end" }}>
                <Text style={[styles.totalsLabel, { color: theme.icon }]}>
                  Gastos
                </Text>
                <Text style={[styles.totalsValue, { color: theme.text }]}>
                  {gastos}
                </Text>
              </View>
            </View>
          </View>
        </View>

        <View style={styles.actionsRow}>
          {renderAction("plus", "Añadir", 0)}
          {renderAction("swap.horizontal", "Transferir", 1)}
          {renderAction("trending.up", "Estadísticas", 2)}
          {renderAction("wallet", "Presupuesto", 3)}
        </View>

        <View style={styles.segmentRow}>
          {(["Día", "Semana", "Mes", "Año"] as const).map((r) => (
            <Pressable
              key={r}
              onPress={() => setRange(r)}
              style={[
                styles.segment,
                {
                  backgroundColor:
                    range === r ? theme.cardBackground : theme.inputBackground,
                  borderColor: range === r ? theme.tint : "transparent",
                },
              ]}
            >
              <Text
                style={{
                  color: range === r ? theme.text : theme.icon,
                  fontWeight: range === r ? "700" : "500",
                }}
              >
                {r}
              </Text>
            </Pressable>
          ))}
        </View>

        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Transacciones Recientes
          </Text>
          <Text style={[styles.viewAll, { color: theme.tint }]}>Ver todas</Text>
        </View>

        <FlatList
          data={recentTransactions}
          keyExtractor={(i) => i.id}
          renderItem={renderRecentTransaction}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          contentContainerStyle={{ paddingBottom: 24 }}
        />

        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            ⚠️ Alertas de Presupuesto
          </Text>
          <Text style={[styles.viewAll, { color: theme.tint }]}>Gestionar</Text>
        </View>

        <FlatList
          data={budgetAlerts}
          keyExtractor={(i) => i.id}
          renderItem={renderBudgetAlert}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          contentContainerStyle={{ paddingBottom: 24 }}
        />

        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            🎯 Metas de Ahorro
          </Text>
          <Text style={[styles.viewAll, { color: theme.tint }]}>
            Nueva meta
          </Text>
        </View>

        <FlatList
          data={savingsGoals}
          keyExtractor={(i) => i.id}
          renderItem={renderSavingsGoal}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          contentContainerStyle={{ paddingBottom: 24 }}
        />

        <View style={styles.sectionHeader}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>
            Gastos por Categoría
          </Text>
          <Text style={[styles.viewAll, { color: theme.tint }]}>Ver todas</Text>
        </View>

        <FlatList
          data={categoryExpenses}
          keyExtractor={(i) => i.id}
          renderItem={renderCategory}
          scrollEnabled={false}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          contentContainerStyle={{ paddingBottom: 24 }}
          ListEmptyComponent={
            <Text style={{ color: theme.icon, textAlign: "center", paddingVertical: 20 }}>
              No hay gastos registrados
            </Text>
          }
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 18,
  },
  menuButton: {
    width: 48,
    height: 48,
    padding: 10,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.12)", 6),
  },
  greeting: {
    fontSize: 28,
    fontWeight: "800",
  },
  subGreeting: {
    fontSize: 14,
    marginTop: 4,
  },
  balanceCard: {
    borderRadius: 16,
    padding: 18,
    marginBottom: 18,
    ...createShadow(0, 6, 14, "rgba(0,0,0,0.22)", 12),
  },
  balanceHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  balanceLabel: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1,
  },
  changePill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  balanceAmount: {
    fontSize: 36,
    fontWeight: "800",
    marginTop: 12,
    marginBottom: 12,
  },
  balanceDivider: {
    height: 1,
    backgroundColor: "rgba(128,128,128,0.2)",
    marginVertical: 8,
  },
  totalsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  totalsItem: {
    flexDirection: "row",
    alignItems: "center",
  },
  totalsLabel: {
    fontSize: 12,
  },
  totalsValue: {
    fontSize: 16,
    fontWeight: "700",
  },
  actionsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 20,
  },
  action: {
    flex: 1,
    marginHorizontal: 6,
    paddingVertical: 12,
    alignItems: "center",
    borderRadius: 12,
  },
  actionIcon: {
    width: 46,
    height: 46,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 6,
    // subtle lift for the small action tiles to read better on dark backgrounds
    ...createShadow(0, 3, 6, "rgba(0,0,0,0.12)"),
  },
  actionLabel: {
    fontSize: 12,
  },
  segmentRow: {
    flexDirection: "row",
    marginBottom: 14,
    justifyContent: "space-between",
  },
  segment: {
    flex: 1,
    marginHorizontal: 4,
    paddingVertical: 10,
    borderRadius: 999,
    alignItems: "center",
    borderWidth: 1,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  viewAll: {
    fontSize: 13,
    fontWeight: "700",
  },
  categoryCard: {
    padding: 14,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  categoryLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  categoryIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  categoryAmount: {
    fontSize: 13,
    marginTop: 2,
  },
  categoryRight: {
    width: 110,
    alignItems: "flex-end",
  },
  progressBarBg: {
    width: "100%",
    height: 8,
    borderRadius: 999,
    overflow: "hidden",
    marginBottom: 6,
    // default subtle background for progress bars; individual items still override inline when necessary
    backgroundColor: "rgba(0,0,0,0.08)",
  },
  progressBar: {
    height: "100%",
    borderRadius: 999,
  },
  categoryPercent: {
    fontSize: 12,
  },
  transactionItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 14,
    borderRadius: 12,
    marginBottom: 8,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  transactionLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    marginRight: 12,
  },
  transactionIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  transactionTitle: {
    fontSize: 14,
    fontWeight: "700",
  },
  transactionTime: {
    fontSize: 12,
    marginTop: 2,
  },
  transactionAmount: {
    fontSize: 14,
    fontWeight: "800",
  },
  budgetAlert: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 14,
    borderRadius: 12,
    marginBottom: 8,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  budgetAlertLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  budgetAlertEmoji: {
    fontSize: 24,
  },
  budgetAlertName: {
    fontSize: 14,
    fontWeight: "700",
  },
  budgetAlertPercent: {
    fontSize: 12,
    marginTop: 2,
  },
  budgetAlertBadge: {
    width: 36,
    height: 36,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  budgetAlertValue: {
    fontSize: 18,
  },
  savingsCard: {
    padding: 14,
    borderRadius: 12,
    marginBottom: 8,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 4),
  },
  savingsHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  savingsName: {
    fontSize: 15,
    fontWeight: "800",
  },
  savingsAmount: {
    fontSize: 13,
  },
  savingsProgressBg: {
    width: "100%",
    height: 10,
    borderRadius: 999,
    overflow: "hidden",
    marginBottom: 6,
  },
  savingsProgressFill: {
    height: "100%",
    borderRadius: 999,
  },
  savingsPercent: {
    fontSize: 12,
    textAlign: "right",
  },
});
