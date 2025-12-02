import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  ScrollView,
  RefreshControl,
  Alert,
} from "react-native";
import { useRouter } from "expo-router";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useAuth } from "@/contexts/AuthContext";
import {
  getReports,
  generateQuickReport,
  deleteReport,
  type ReportListItem,
} from "shared";

const REPORT_TYPES = [
  {
    id: "monthly_summary",
    title: "Resumen Mensual",
    description: "Ingresos, gastos y balance del mes",
    icon: "calendar",
    color: "#25d1b2",
  },
  {
    id: "category_breakdown",
    title: "Por Categorías",
    description: "Desglose de gastos por categoría",
    icon: "chart.pie",
    color: "#7c4dff",
  },
  {
    id: "income_vs_expenses",
    title: "Ingresos vs Gastos",
    description: "Comparativa de flujo de dinero",
    icon: "arrow.left.arrow.right",
    color: "#ff6b6b",
  },
];

export default function ReportsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();

  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadReports = useCallback(async () => {
    if (!user?.id) return;
    try {
      const data = await getReports(user.id);
      setReports(data);
    } catch (error) {
      console.error("Error loading reports:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    loadReports();
  }, [loadReports]);

  const handleGenerateReport = async (reportType: string) => {
    if (!user?.id) return;

    setIsGenerating(reportType);
    try {
      const report = await generateQuickReport(user.id, reportType, 1);
      if (report) {
        Alert.alert(
          "Reporte Generado",
          report.ai_summary || "Tu reporte está listo.",
          [
            { text: "Ver Detalles", onPress: () => router.push(`/report-detail?id=${report.id}` as any) },
            { text: "OK" },
          ]
        );
        loadReports();
      } else {
        Alert.alert("Error", "No se pudo generar el reporte");
      }
    } catch {
      Alert.alert("Error", "Ocurrió un error al generar el reporte");
    } finally {
      setIsGenerating(null);
    }
  };

  const handleDeleteReport = async (reportId: number) => {
    if (!user?.id) return;

    Alert.alert(
      "Eliminar Reporte",
      "¿Estás seguro de que deseas eliminar este reporte?",
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Eliminar",
          style: "destructive",
          onPress: async () => {
            const deleted = await deleteReport(user.id, reportId);
            if (deleted) {
              setReports((prev) => prev.filter((r) => r.id !== reportId));
            }
          },
        },
      ]
    );
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("es-ES", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  const getReportTypeInfo = (type: string) => {
    return REPORT_TYPES.find((t) => t.id === type) || REPORT_TYPES[0];
  };

  const renderReportTypeCard = (type: typeof REPORT_TYPES[0]) => (
    <Pressable
      key={type.id}
      onPress={() => handleGenerateReport(type.id)}
      disabled={isGenerating !== null}
      style={[
        styles.typeCard,
        {
          backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground,
          borderColor: isDark ? "rgba(255,255,255,0.05)" : "transparent",
          opacity: isGenerating !== null ? 0.7 : 1,
          ...createShadow(0, 4, 8, theme.shadow, 4),
        },
      ]}
    >
      <View style={[styles.typeIconWrap, { backgroundColor: type.color + "22" }]}>
        {isGenerating === type.id ? (
          <ActivityIndicator size="small" color={type.color} />
        ) : (
          <IconSymbol name={type.icon as any} size={24} color={type.color} />
        )}
      </View>
      <ThemedText style={[styles.typeTitle, { color: theme.text }]}>
        {type.title}
      </ThemedText>
      <ThemedText style={[styles.typeDesc, { color: theme.icon }]}>
        {type.description}
      </ThemedText>
    </Pressable>
  );

  const renderReportItem = ({ item }: { item: ReportListItem }) => {
    const typeInfo = getReportTypeInfo(item.report_type);

    return (
      <Pressable
        onPress={() => router.push(`/report-detail?id=${item.id}` as any)}
        onLongPress={() => handleDeleteReport(item.id)}
        style={[
          styles.reportRow,
          {
            backgroundColor: isDark ? "#1f1f1f" : theme.cardBackground,
            ...createShadow(0, 4, 8, theme.shadow, 4),
          },
        ]}
      >
        <View style={styles.reportLeft}>
          <View style={[styles.reportIconWrap, { backgroundColor: typeInfo.color + "22" }]}>
            <IconSymbol name={typeInfo.icon as any} size={18} color={typeInfo.color} />
          </View>
          <View style={{ marginLeft: 12, flex: 1 }}>
            <ThemedText style={[styles.reportTitle, { color: theme.text }]} numberOfLines={1}>
              {item.title}
            </ThemedText>
            <ThemedText style={[styles.reportSubtitle, { color: theme.icon }]}>
              {formatDate(item.period_start)} - {formatDate(item.period_end)}
            </ThemedText>
          </View>
        </View>

        <View style={styles.reportRight}>
          <View
            style={[
              styles.statusBadge,
              {
                backgroundColor:
                  item.status === "completed"
                    ? "#25d1b222"
                    : item.status === "generating"
                    ? "#ffb86b22"
                    : "#ff6b6b22",
              },
            ]}
          >
            <ThemedText
              style={[
                styles.statusText,
                {
                  color:
                    item.status === "completed"
                      ? "#25d1b2"
                      : item.status === "generating"
                      ? "#ffb86b"
                      : "#ff6b6b",
                },
              ]}
            >
              {item.status === "completed" ? "Listo" : item.status === "generating" ? "Generando" : "Error"}
            </ThemedText>
          </View>
          <ThemedText style={[styles.reportDate, { color: theme.icon }]}>
            {formatDate(item.created_at)}
          </ThemedText>
        </View>
      </Pressable>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View
        style={[
          styles.emptyStateIcon,
          { backgroundColor: isDark ? "rgba(124, 77, 255, 0.16)" : "rgba(124, 77, 255, 0.08)" },
        ]}
      >
        <IconSymbol name={"doc.text" as any} size={32} color={theme.icon} />
      </View>
      <ThemedText style={[styles.emptyStateTitle, { color: theme.text }]}>
        Sin reportes
      </ThemedText>
      <ThemedText style={[styles.emptyStateSubtitle, { color: theme.icon }]}>
        Genera tu primer reporte financiero arriba
      </ThemedText>
    </View>
  );

  if (!user) return null;

  return (
    <ThemedView style={[styles.container, { backgroundColor: theme.background }]}>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 40 }}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} tintColor={theme.tint} />
        }
      >
        <View style={styles.header}>
          <ThemedText type="title" style={[styles.title, { color: theme.text }]}>
            Reportes
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            Genera y exporta informes sobre tus finanzas
          </ThemedText>
        </View>

        {/* Report Type Cards */}
        <View style={styles.typeCardsContainer}>
          <ThemedText style={[styles.sectionTitle, { color: theme.text }]}>
            Generar Nuevo Reporte
          </ThemedText>
          <View style={styles.typeCards}>
            {REPORT_TYPES.map(renderReportTypeCard)}
          </View>
        </View>

        {/* Previous Reports */}
        <View style={styles.reportsSection}>
          <ThemedText style={[styles.sectionTitle, { color: theme.text }]}>
            Reportes Anteriores
          </ThemedText>

          {isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={theme.tint} />
            </View>
          ) : reports.length === 0 ? (
            renderEmptyState()
          ) : (
            <View>
              {reports.map((report) => (
                <View key={report.id} style={{ marginBottom: 12 }}>
                  {renderReportItem({ item: report })}
                </View>
              ))}
            </View>
          )}
        </View>
      </ScrollView>
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
    paddingBottom: 12,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
  },
  subtitle: {
    fontSize: 13,
    marginTop: 6,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 12,
    paddingHorizontal: 20,
  },
  typeCardsContainer: {
    marginTop: 16,
  },
  typeCards: {
    flexDirection: "row",
    paddingHorizontal: 16,
    gap: 12,
  },
  typeCard: {
    flex: 1,
    padding: 16,
    borderRadius: 16,
    alignItems: "center",
    borderWidth: 1,
  },
  typeIconWrap: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  typeTitle: {
    fontSize: 13,
    fontWeight: "700",
    textAlign: "center",
    marginBottom: 4,
  },
  typeDesc: {
    fontSize: 11,
    textAlign: "center",
    lineHeight: 14,
  },
  reportsSection: {
    marginTop: 24,
    paddingHorizontal: 20,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: "center",
  },
  reportRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    justifyContent: "space-between",
  },
  reportLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  reportIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  reportTitle: {
    fontSize: 15,
    fontWeight: "700",
  },
  reportSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  reportRight: {
    alignItems: "flex-end",
    marginLeft: 12,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginBottom: 4,
  },
  statusText: {
    fontSize: 11,
    fontWeight: "700",
  },
  reportDate: {
    fontSize: 11,
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 40,
  },
  emptyStateIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 4,
  },
  emptyStateSubtitle: {
    fontSize: 13,
    textAlign: "center",
  },
});
