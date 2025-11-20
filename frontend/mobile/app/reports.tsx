import React, { useMemo } from "react";
import { View, StyleSheet, Pressable, FlatList } from "react-native";
import { useRouter } from "expo-router";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { IconSymbol } from "@/components/ui/icon-symbol";

type ReportItem = {
  id: string;
  title: string;
  subtitle?: string;
  date: string;
};

export default function ReportsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];

  const reports: ReportItem[] = useMemo(
    () => [
      {
        id: "r1",
        title: "Resumen mensual",
        subtitle: "Enero 2025 - Ingresos / Gastos",
        date: "2025-01-31",
      },
      {
        id: "r2",
        title: "Reporte por categoría",
        subtitle: "Comparativo trimestral",
        date: "2025-03-31",
      },
      {
        id: "r3",
        title: "Historial de transacciones",
        subtitle: "Exportación CSV",
        date: "2025-04-07",
      },
    ],
    [],
  );

  const handleGenerate = (id?: string) => {
    // placeholder action: navigate to a preview or start generation flow
    if (id) {
      router.push(`/reports/${id}` as any);
    } else {
      // generic generate — navigates to a create screen or triggers an API job
      router.push("/reports/create" as any);
    }
  };

  const renderItem = ({ item }: { item: ReportItem }) => (
    <Pressable
      style={[
        styles.reportRow,
        { backgroundColor: theme.cardBackground, shadowColor: theme.shadow },
      ]}
      onPress={() => handleGenerate(item.id)}
    >
      <View style={styles.reportLeft}>
        <IconSymbol name={"document" as any} size={20} color={theme.tint} />
        <View style={{ marginLeft: 12 }}>
          <ThemedText style={[styles.reportTitle, { color: theme.text }]}>
            {item.title}
          </ThemedText>
          {item.subtitle ? (
            <ThemedText style={[styles.reportSubtitle, { color: theme.icon }]}>
              {item.subtitle}
            </ThemedText>
          ) : null}
        </View>
      </View>

      <View style={styles.reportRight}>
        <ThemedText style={{ color: theme.icon }}>{item.date}</ThemedText>
        <Pressable
          onPress={() => handleGenerate(item.id)}
          style={({ pressed }) => [
            styles.generateButton,
            {
              backgroundColor: pressed ? theme.inputBackground : theme.tint,
              opacity: pressed ? 0.85 : 1,
            },
          ]}
        >
          <ThemedText style={{ color: "#fff", fontWeight: "700" }}>
            Generar
          </ThemedText>
        </Pressable>
      </View>
    </Pressable>
  );

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.header}>
        <ThemedText type="title" style={[styles.title, { color: theme.text }]}>
          Reportes
        </ThemedText>
        <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
          Genera y exporta informes sobre tus finanzas
        </ThemedText>
      </View>

      <View style={styles.actionsRow}>
        <Pressable
          onPress={() => handleGenerate()}
          style={({ pressed }) => [
            styles.primaryAction,
            { backgroundColor: pressed ? theme.inputBackground : theme.tint },
          ]}
        >
          <IconSymbol name={"document" as any} size={18} color={"#fff"} />
          <ThemedText style={styles.primaryActionLabel}>
            Nuevo reporte
          </ThemedText>
        </Pressable>

        <Pressable
          onPress={() => router.push("/reports/export" as any)}
          style={({ pressed }) => [
            styles.secondaryAction,
            {
              backgroundColor: pressed
                ? theme.inputBackground
                : theme.cardBackground,
              borderColor: theme.icon,
            },
          ]}
        >
          <IconSymbol name={"download" as any} size={18} color={theme.icon} />
          <ThemedText
            style={[styles.secondaryActionLabel, { color: theme.icon }]}
          >
            Exportar todos
          </ThemedText>
        </Pressable>
      </View>

      <FlatList
        data={reports}
        keyExtractor={(r) => r.id}
        renderItem={renderItem}
        contentContainerStyle={{ padding: 20, paddingBottom: 120 }}
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
  actionsRow: {
    flexDirection: "row",
    paddingHorizontal: 20,
    justifyContent: "space-between",
    marginBottom: 12,
  },
  primaryAction: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 12,
    minWidth: 140,
    justifyContent: "center",
  },
  primaryActionLabel: {
    color: "#fff",
    fontWeight: "700",
    marginLeft: 8,
  },
  secondaryAction: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 12,
    minWidth: 140,
    justifyContent: "center",
    borderWidth: 1,
  },
  secondaryActionLabel: {
    marginLeft: 8,
    fontWeight: "700",
  },
  reportRow: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    justifyContent: "space-between",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  reportLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  reportTitle: {
    fontSize: 16,
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
  generateButton: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
});
