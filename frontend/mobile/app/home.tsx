import { useMemo, useState, useEffect, useCallback } from "react";
import {
  View,
  StyleSheet,
  Text,
  Pressable,
  FlatList,
  ScrollView,
  ActivityIndicator,
} from "react-native";
import { useRouter } from "expo-router";
import { SafeAreaView } from "react-native-safe-area-context";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import { getTransactions, getCategories, getSources, getFinancialHealth, type FinancialHealth } from "shared";

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

const formatAmountShort = (amount: number): string => {
  if (amount >= 1_000_000_000) {
    return (amount / 1_000_000_000).toFixed(1) + "B";
  } else if (amount >= 1_000_000) {
    return (amount / 1_000_000).toFixed(1) + "M";
  } else if (amount >= 10_000) {
    return (amount / 1_000).toFixed(1) + "K";
  }
  return amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
};

export default function HomeScreen() {
  const router = useRouter();
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
  const [financialHealth, setFinancialHealth] = useState<FinancialHealth | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState(false);

  const loadFinancialHealth = useCallback(async () => {
    if (!user?.id) return;
    setIsLoadingHealth(true);
    try {
      const health = await getFinancialHealth(user.id, 30);
      setFinancialHealth(health);
    } catch (error) {
      console.error("Error loading financial health:", error);
    } finally {
      setIsLoadingHealth(false);
    }
  }, [user?.id]);

  useEffect(() => {
    if (user?.id) {
      getTransactions(user.id).then((data) => setRecentTransactions(data));
      getCategories().then((data) => setBackendCategories(data));
      getSources().then((data) => setBackendSources(data));
      loadFinancialHealth();
    }
  }, [user?.id, loadFinancialHealth]);

  const getCategoryName = (id: number) => {
    const cat = backendCategories.find((c) => c.id === id);
    return cat?.name || "Sin categoría";
  };

  const getSourceName = (id: number) => {
    const src = backendSources.find((s) => s.id === id);
    return src?.name || "Sin fuente";
  };

  // Calculate real totals from transactions
  const { totalIncome, totalExpenses, totalBalance, balanceChange } = useMemo(() => {
    let income = 0;
    let expenses = 0;

    recentTransactions.forEach((tx) => {
      if (tx.transaction_type === "income") {
        income += tx.amount;
      } else {
        expenses += tx.amount;
      }
    });

    const balance = income - expenses;
    // Calculate percentage change (using expenses as reference for simplicity)
    const change = income > 0 ? ((balance / income) * 100).toFixed(1) : "0";

    return {
      totalIncome: income,
      totalExpenses: expenses,
      totalBalance: balance,
      balanceChange: balance >= 0 ? `+${change}%` : `${change}%`,
    };
  }, [recentTransactions]);

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

    const expensesTotal = Object.values(expensesByCategory).reduce((sum, val) => sum + val, 0);

    // Map backend categories to display format with calculated amounts
    return backendCategories
      .filter((cat) => expensesByCategory[cat.id] !== undefined)
      .map((cat, index) => {
        const amount = expensesByCategory[cat.id] || 0;
        const percent = expensesTotal > 0 ? Math.round((amount / expensesTotal) * 100) : 0;
        const lowerName = cat.name.toLowerCase();
        
        return {
          id: cat.id.toString(),
          name: cat.name,
          amount: `$${formatAmountShort(amount)}`,
          percent,
          color: CATEGORY_COLORS[index % CATEGORY_COLORS.length],
          emoji: CATEGORY_EMOJIS[lowerName] || "🏷️",
        };
      })
      .sort((a, b) => b.percent - a.percent);
  }, [backendCategories, recentTransactions]);

  const budgetAlerts = useMemo(() => [], []);

  const savingsGoals = useMemo(() => [], []);

  if (!user) return null;

  // Format currency for display
  const formatCurrency = (amount: number) => {
    const absAmount = Math.abs(amount);
    let formatted: string;
    if (absAmount >= 1_000_000_000) {
      formatted = (absAmount / 1_000_000_000).toFixed(1) + "B";
    } else if (absAmount >= 1_000_000) {
      formatted = (absAmount / 1_000_000).toFixed(1) + "M";
    } else if (absAmount >= 10_000) {
      formatted = (absAmount / 1_000).toFixed(1) + "K";
    } else {
      formatted = absAmount.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      });
    }
    return amount < 0 ? `-$${formatted}` : `$${formatted}`;
  };

  const formatAmount = (amount: number): string => {
    if (amount >= 1_000_000_000) {
      return (amount / 1_000_000_000).toFixed(1) + "B";
    } else if (amount >= 1_000_000) {
      return (amount / 1_000_000).toFixed(1) + "M";
    } else if (amount >= 10_000) {
      return (amount / 1_000).toFixed(1) + "K";
    }
    return amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

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
          {isIncome ? "+" : "-"}${formatAmount(item.amount)}
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
        contentContainerStyle={{ padding: 20, paddingTop: 12 }}
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
                { backgroundColor: totalBalance >= 0 ? (isDark ? "#023a31" : "#e6faf3") : (isDark ? "#3a0202" : "#fae6e6") },
              ]}
            >
              <Text
                style={{
                  color: totalBalance >= 0 ? (isDark ? "#7af0c9" : "#0f5132") : (isDark ? "#ff8a8a" : "#721c24"),
                  fontWeight: "700",
                }}
              >
                {balanceChange}
              </Text>
            </View>
          </View>

          <Text style={[styles.balanceAmount, { color: theme.text }]}>
            {formatCurrency(totalBalance)}
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
                  {formatCurrency(totalIncome)}
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
                  {formatCurrency(totalExpenses)}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Financial Health Card */}
        <View
          style={[
            styles.healthCard,
            {
              backgroundColor: isDark ? "#222" : theme.cardBackground,
              ...createShadow(0, 6, 14, isDark ? "rgba(0,0,0,0.7)" : theme.shadow, 12),
            },
          ]}
        >
          <View style={styles.healthHeader}>
            <View style={styles.healthTitleRow}>
              <IconSymbol name={"heart.fill" as any} size={20} color={financialHealth?.status_color || theme.tint} />
              <Text style={[styles.healthTitle, { color: theme.text }]}>
                Salud Financiera
              </Text>
            </View>
            <Pressable onPress={loadFinancialHealth} disabled={isLoadingHealth}>
              <IconSymbol 
                name={"arrow.clockwise" as any} 
                size={18} 
                color={isLoadingHealth ? theme.icon : theme.tint} 
              />
            </Pressable>
          </View>

          {isLoadingHealth ? (
            <View style={styles.healthLoading}>
              <ActivityIndicator size="small" color={theme.tint} />
              <Text style={[styles.healthLoadingText, { color: theme.icon }]}>
                Analizando tus finanzas...
              </Text>
            </View>
          ) : financialHealth ? (
            <>
              <View style={styles.healthScoreContainer}>
                <View style={styles.healthScoreCircle}>
                  <View
                    style={[
                      styles.healthScoreInner,
                      {
                        backgroundColor: isDark ? "#1a1a1a" : "#fff",
                        borderColor: financialHealth.status_color,
                      },
                    ]}
                  >
                    <Text style={[styles.healthScoreNumber, { color: financialHealth.status_color }]}>
                      {financialHealth.score}
                    </Text>
                    <Text style={[styles.healthScoreLabel, { color: theme.icon }]}>
                      de 100
                    </Text>
                  </View>
                </View>
                <View style={styles.healthScoreInfo}>
                  <View
                    style={[
                      styles.healthStatusBadge,
                      { backgroundColor: financialHealth.status_color + "22" },
                    ]}
                  >
                    <Text style={[styles.healthStatusText, { color: financialHealth.status_color }]}>
                      {financialHealth.status === "excellent" && "Excelente"}
                      {financialHealth.status === "good" && "Bueno"}
                      {financialHealth.status === "fair" && "Regular"}
                      {financialHealth.status === "needs_attention" && "Atención"}
                      {financialHealth.status === "critical" && "Crítico"}
                      {financialHealth.status === "sin_datos" && "Sin datos"}
                    </Text>
                  </View>
                  <Text style={[styles.healthSavingsRate, { color: theme.text }]}>
                    Tasa de ahorro: {financialHealth.savings_rate}%
                  </Text>
                </View>
              </View>

              <View style={styles.healthDivider} />

              <View style={styles.healthAiSection}>
                <View style={styles.healthAiHeader}>
                  <IconSymbol name={"sparkles" as any} size={14} color={theme.tint} />
                  <Text style={[styles.healthAiTitle, { color: theme.tint }]}>
                    Análisis IA
                  </Text>
                </View>
                <Text style={[styles.healthAiSummary, { color: theme.text }]}>
                  {financialHealth.ai_summary}
                </Text>
              </View>

              {financialHealth.ai_recommendations.length > 0 && (
                <View style={styles.healthRecommendations}>
                  {financialHealth.ai_recommendations.map((rec, index) => (
                    <View
                      key={index}
                      style={[
                        styles.healthRecItem,
                        { backgroundColor: isDark ? "#2a2a2a" : "#f8f9fa" },
                      ]}
                    >
                      <Text style={styles.healthRecIcon}>💡</Text>
                      <Text style={[styles.healthRecText, { color: theme.text }]}>
                        {rec}
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </>
          ) : (
            <View style={styles.healthEmpty}>
              <IconSymbol name={"chart.bar" as any} size={32} color={theme.icon} />
              <Text style={[styles.healthEmptyText, { color: theme.icon }]}>
                Registra transacciones para ver tu salud financiera
              </Text>
            </View>
          )}
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
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View
                style={[
                  styles.emptyStateIcon,
                  {
                    backgroundColor: isDark
                      ? "rgba(37, 209, 178, 0.16)"
                      : "rgba(37, 209, 178, 0.08)",
                  },
                ]}
              >
                <IconSymbol name={"tray"} size={22} color={theme.tint} />
              </View>
              <Text style={[styles.emptyStateTitle, { color: theme.text }]}>
                Aún no tienes transacciones
              </Text>
              <Text
                style={[styles.emptyStateSubtitle, { color: theme.icon }]}
              >
                Registra tu primera transacción para verla aquí.
              </Text>
            </View>
          }
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
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View
                style={[
                  styles.emptyStateIcon,
                  {
                    backgroundColor: isDark
                      ? "rgba(255, 107, 107, 0.16)"
                      : "rgba(255, 107, 107, 0.08)",
                  },
                ]}
              >
                <IconSymbol name={"bell"} size={22} color="#ff6b6b" />
              </View>
              <Text style={[styles.emptyStateTitle, { color: theme.text }]}>
                Sin alertas activas
              </Text>
              <Text
                style={[styles.emptyStateSubtitle, { color: theme.icon }]}
              >
                Configura presupuestos para recibir alertas.
              </Text>
            </View>
          }
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
          ListEmptyComponent={
            <View style={styles.emptyState}>
              <View
                style={[
                  styles.emptyStateIcon,
                  {
                    backgroundColor: isDark
                      ? "rgba(139, 195, 74, 0.16)"
                      : "rgba(139, 195, 74, 0.08)",
                  },
                ]}
              >
                <IconSymbol name={"flag"} size={22} color="#8bc34a" />
              </View>
              <Text style={[styles.emptyStateTitle, { color: theme.text }]}>
                Sin metas de ahorro
              </Text>
              <Text
                style={[styles.emptyStateSubtitle, { color: theme.icon }]}
              >
                Crea una meta para comenzar a ahorrar.
              </Text>
            </View>
          }
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
            <View style={styles.emptyState}>
              <View
                style={[
                  styles.emptyStateIcon,
                  {
                    backgroundColor: isDark
                      ? "rgba(124, 77, 255, 0.16)"
                      : "rgba(124, 77, 255, 0.08)",
                  },
                ]}
              >
                <IconSymbol name={"chart.pie"} size={22} color="#7c4dff" />
              </View>
              <Text style={[styles.emptyStateTitle, { color: theme.text }]}>
                Sin gastos por categoría
              </Text>
              <Text
                style={[styles.emptyStateSubtitle, { color: theme.icon }]}
              >
                Registra gastos para ver el desglose.
              </Text>
            </View>
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
  emptyState: {
    alignItems: "center",
    paddingVertical: 32,
    paddingHorizontal: 16,
  },
  emptyStateIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  emptyStateTitle: {
    fontSize: 16,
    fontWeight: "700",
    textAlign: "center",
    marginBottom: 4,
  },
  emptyStateSubtitle: {
    fontSize: 13,
    textAlign: "center",
    lineHeight: 18,
  },
  // Financial Health Card Styles
  healthCard: {
    borderRadius: 16,
    padding: 18,
    marginBottom: 18,
  },
  healthHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  healthTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  healthTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  healthLoading: {
    alignItems: "center",
    paddingVertical: 24,
    gap: 12,
  },
  healthLoadingText: {
    fontSize: 13,
  },
  healthScoreContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
  },
  healthScoreCircle: {
    width: 90,
    height: 90,
  },
  healthScoreInner: {
    width: 90,
    height: 90,
    borderRadius: 45,
    borderWidth: 4,
    alignItems: "center",
    justifyContent: "center",
  },
  healthScoreNumber: {
    fontSize: 28,
    fontWeight: "800",
  },
  healthScoreLabel: {
    fontSize: 11,
    marginTop: -2,
  },
  healthScoreInfo: {
    flex: 1,
    gap: 8,
  },
  healthStatusBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 999,
  },
  healthStatusText: {
    fontSize: 13,
    fontWeight: "700",
  },
  healthSavingsRate: {
    fontSize: 14,
    fontWeight: "600",
  },
  healthDivider: {
    height: 1,
    backgroundColor: "rgba(128,128,128,0.2)",
    marginVertical: 14,
  },
  healthAiSection: {
    marginBottom: 12,
  },
  healthAiHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 8,
  },
  healthAiTitle: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  healthAiSummary: {
    fontSize: 14,
    lineHeight: 20,
  },
  healthRecommendations: {
    gap: 8,
  },
  healthRecItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    padding: 12,
    borderRadius: 10,
    gap: 10,
  },
  healthRecIcon: {
    fontSize: 14,
  },
  healthRecText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  healthEmpty: {
    alignItems: "center",
    paddingVertical: 24,
    gap: 12,
  },
  healthEmptyText: {
    fontSize: 13,
    textAlign: "center",
  },
});
