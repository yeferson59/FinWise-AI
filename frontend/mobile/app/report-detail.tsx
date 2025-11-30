import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  StyleSheet,
  ScrollView,
  Pressable,
  ActivityIndicator,
  Share,
  Alert,
} from "react-native";
import { useRouter, useLocalSearchParams } from "expo-router";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useAuth } from "@/contexts/AuthContext";
import { getReport, getReportCsvUrl, type Report } from "shared";

export default function ReportDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();

  const [report, setReport] = useState<Report | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadReport = useCallback(async () => {
    if (!user?.id || !id) return;
    try {
      const data = await getReport(user.id, parseInt(id));
      setReport(data);
    } catch (error) {
      console.error("Error loading report:", error);
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, id]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  const handleShare = async () => {
    if (!report) return;

    try {
      await Share.share({
        message: `📊 ${report.title}\n\n${report.ai_summary || ""}\n\n💰 Ingresos: $${report.data?.total_income.toFixed(2)}\n💸 Gastos: $${report.data?.total_expenses.toFixed(2)}\n📈 Balance: $${report.data?.net_balance.toFixed(2)}`,
        title: report.title,
      });
    } catch (error) {
      console.error("Error sharing:", error);
    }
  };

  const handleExportCSV = () => {
    if (!user?.id || !report) return;
    const url = getReportCsvUrl(user.id, report.id);
    Alert.alert(
      "Exportar CSV",
      "El archivo CSV está disponible en:\n" + url,
      [{ text: "OK" }]
    );
  };

  const formatCurrency = (amount: number) => {
    return `$${amount.toLocaleString("es-ES", { minimumFractionDigits: 2 })}`;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("es-ES", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };

  if (!user) return null;

  if (isLoading) {
    return (
      <ThemedView style={[styles.container, styles.centered, { backgroundColor: theme.background }]}>
        <ActivityIndicator size="large" color={theme.tint} />
      </ThemedView>
    );
  }

  if (!report) {
    return (
      <ThemedView style={[styles.container, styles.centered, { backgroundColor: theme.background }]}>
        <IconSymbol name={"exclamationmark.triangle" as any} size={48} color={theme.icon} />
        <ThemedText style={[styles.errorText, { color: theme.text }]}>
          Reporte no encontrado
        </ThemedText>
        <Pressable onPress={() => router.back()} style={[styles.backButton, { backgroundColor: theme.tint }]}>
          <ThemedText style={{ color: isDark ? "#1a1a1a" : "#fff", fontWeight: "700" }}>
            Volver
          </ThemedText>
        </Pressable>
      </ThemedView>
    );
  }

  const data = report.data;

  return (
    <ThemedView style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={{ paddingBottom: 40 }}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={() => router.back()} style={styles.backBtn}>
            <IconSymbol name={"chevron.left" as any} size={24} color={theme.tint} />
          </Pressable>
          <View style={{ flex: 1 }}>
            <ThemedText style={[styles.title, { color: theme.text }]} numberOfLines={1}>
              {report.title}
            </ThemedText>
            <ThemedText style={[styles.period, { color: theme.icon }]}>
              {formatDate(report.period_start)} - {formatDate(report.period_end)}
            </ThemedText>
          </View>
          <Pressable onPress={handleShare} style={styles.shareBtn}>
            <IconSymbol name={"square.and.arrow.up" as any} size={20} color={theme.tint} />
          </Pressable>
        </View>

        {/* AI Summary */}
        {report.ai_summary && (
          <View
            style={[
              styles.summaryCard,
              {
                backgroundColor: isDark ? "#1a2e35" : "#e8f5f0",
                borderColor: isDark ? "#25d1b244" : "#25d1b2",
              },
            ]}
          >
            <View style={styles.summaryHeader}>
              <IconSymbol name={"sparkles" as any} size={16} color="#25d1b2" />
              <ThemedText style={[styles.summaryTitle, { color: "#25d1b2" }]}>
                Resumen IA
              </ThemedText>
            </View>
            <ThemedText style={[styles.summaryText, { color: theme.text }]}>
              {report.ai_summary}
            </ThemedText>
          </View>
        )}

        {/* Main Stats */}
        {data && (
          <>
            <View style={styles.statsGrid}>
              <View style={[styles.statCard, { backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground }]}>
                <IconSymbol name={"arrow.down.circle.fill" as any} size={24} color="#25d1b2" />
                <ThemedText style={[styles.statLabel, { color: theme.icon }]}>Ingresos</ThemedText>
                <ThemedText style={[styles.statValue, { color: "#25d1b2" }]}>
                  {formatCurrency(data.total_income)}
                </ThemedText>
              </View>
              <View style={[styles.statCard, { backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground }]}>
                <IconSymbol name={"arrow.up.circle.fill" as any} size={24} color="#ff6b6b" />
                <ThemedText style={[styles.statLabel, { color: theme.icon }]}>Gastos</ThemedText>
                <ThemedText style={[styles.statValue, { color: "#ff6b6b" }]}>
                  {formatCurrency(data.total_expenses)}
                </ThemedText>
              </View>
            </View>

            <View style={styles.statsGrid}>
              <View style={[styles.statCard, { backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground }]}>
                <IconSymbol name={"chart.line.uptrend.xyaxis" as any} size={24} color="#7c4dff" />
                <ThemedText style={[styles.statLabel, { color: theme.icon }]}>Balance</ThemedText>
                <ThemedText
                  style={[styles.statValue, { color: data.net_balance >= 0 ? "#25d1b2" : "#ff6b6b" }]}
                >
                  {formatCurrency(data.net_balance)}
                </ThemedText>
              </View>
              <View style={[styles.statCard, { backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground }]}>
                <IconSymbol name={"percent" as any} size={24} color="#ffb86b" />
                <ThemedText style={[styles.statLabel, { color: theme.icon }]}>Ahorro</ThemedText>
                <ThemedText style={[styles.statValue, { color: "#ffb86b" }]}>
                  {data.savings_rate}%
                </ThemedText>
              </View>
            </View>

            {/* Category Breakdown */}
            {data.category_breakdown.length > 0 && (
              <View style={styles.section}>
                <ThemedText style={[styles.sectionTitle, { color: theme.text }]}>
                  Gastos por Categoría
                </ThemedText>
                {data.category_breakdown.slice(0, 5).map((cat, index) => (
                  <View
                    key={cat.category_id}
                    style={[
                      styles.categoryRow,
                      { backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground },
                    ]}
                  >
                    <View style={styles.categoryLeft}>
                      <View
                        style={[
                          styles.categoryRank,
                          { backgroundColor: theme.tint + "22" },
                        ]}
                      >
                        <ThemedText style={{ color: theme.tint, fontWeight: "700" }}>
                          {index + 1}
                        </ThemedText>
                      </View>
                      <View>
                        <ThemedText style={[styles.categoryName, { color: theme.text }]}>
                          {cat.category_name}
                        </ThemedText>
                        <ThemedText style={[styles.categoryCount, { color: theme.icon }]}>
                          {cat.transaction_count} transacciones
                        </ThemedText>
                      </View>
                    </View>
                    <View style={styles.categoryRight}>
                      <ThemedText style={[styles.categoryAmount, { color: theme.text }]}>
                        {formatCurrency(cat.total_amount)}
                      </ThemedText>
                      <ThemedText style={[styles.categoryPercent, { color: theme.icon }]}>
                        {cat.percentage.toFixed(1)}%
                      </ThemedText>
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Monthly Trends */}
            {data.monthly_trends.length > 0 && (
              <View style={styles.section}>
                <ThemedText style={[styles.sectionTitle, { color: theme.text }]}>
                  Tendencia Mensual
                </ThemedText>
                {data.monthly_trends.map((trend) => (
                  <View
                    key={`${trend.year}-${trend.month}`}
                    style={[
                      styles.trendRow,
                      { backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground },
                    ]}
                  >
                    <ThemedText style={[styles.trendMonth, { color: theme.text }]}>
                      {trend.month}/{trend.year}
                    </ThemedText>
                    <View style={styles.trendValues}>
                      <ThemedText style={{ color: "#25d1b2", fontSize: 12 }}>
                        +{formatCurrency(trend.income)}
                      </ThemedText>
                      <ThemedText style={{ color: "#ff6b6b", fontSize: 12 }}>
                        -{formatCurrency(trend.expenses)}
                      </ThemedText>
                      <ThemedText
                        style={{
                          color: trend.balance >= 0 ? "#25d1b2" : "#ff6b6b",
                          fontWeight: "700",
                          fontSize: 13,
                        }}
                      >
                        {formatCurrency(trend.balance)}
                      </ThemedText>
                    </View>
                  </View>
                ))}
              </View>
            )}
          </>
        )}

        {/* Export Button */}
        <View style={styles.exportSection}>
          <Pressable
            onPress={handleExportCSV}
            style={[styles.exportButton, { backgroundColor: theme.tint }]}
          >
            <IconSymbol name={"arrow.down.doc" as any} size={18} color={isDark ? "#1a1a1a" : "#fff"} />
            <ThemedText style={[styles.exportText, { color: isDark ? "#1a1a1a" : "#fff" }]}>
              Exportar CSV
            </ThemedText>
          </Pressable>
        </View>
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    justifyContent: "center",
    alignItems: "center",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    gap: 12,
  },
  backBtn: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  shareBtn: {
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
  },
  period: {
    fontSize: 12,
    marginTop: 2,
  },
  summaryCard: {
    marginHorizontal: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  summaryHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  summaryTitle: {
    fontSize: 13,
    fontWeight: "700",
  },
  summaryText: {
    fontSize: 14,
    lineHeight: 20,
  },
  statsGrid: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginTop: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  statLabel: {
    fontSize: 12,
    marginTop: 8,
  },
  statValue: {
    fontSize: 18,
    fontWeight: "800",
    marginTop: 4,
  },
  section: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 12,
  },
  categoryRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 12,
    borderRadius: 10,
    marginBottom: 8,
  },
  categoryLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  categoryRank: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  categoryName: {
    fontSize: 14,
    fontWeight: "600",
  },
  categoryCount: {
    fontSize: 11,
    marginTop: 2,
  },
  categoryRight: {
    alignItems: "flex-end",
  },
  categoryAmount: {
    fontSize: 14,
    fontWeight: "700",
  },
  categoryPercent: {
    fontSize: 11,
    marginTop: 2,
  },
  trendRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 12,
    borderRadius: 10,
    marginBottom: 8,
  },
  trendMonth: {
    fontSize: 14,
    fontWeight: "600",
  },
  trendValues: {
    flexDirection: "row",
    gap: 16,
    alignItems: "center",
  },
  exportSection: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  exportButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 14,
    borderRadius: 12,
    gap: 8,
  },
  exportText: {
    fontWeight: "700",
  },
  errorText: {
    fontSize: 16,
    marginTop: 16,
    marginBottom: 16,
  },
  backButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
  },
});
