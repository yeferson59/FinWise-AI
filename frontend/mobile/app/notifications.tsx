import React, { useMemo, useState } from "react";
import {
  View,
  StyleSheet,
  FlatList,
  Pressable,
  Text,
  Platform,
} from "react-native";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

type NotificationItem = {
  id: string;
  title: string;
  body: string;
  date: string;
  read: boolean;
  icon?: string;
};

export default function NotificationsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const initial = useMemo<NotificationItem[]>(
    () => [
      {
        id: "1",
        title: "Transacción registrada",
        body: "Pago con tarjeta en Supermercado - $45.20",
        date: "Hoy • 09:24",
        read: false,
        icon: "creditcard.fill",
      },
      {
        id: "2",
        title: "Reporte mensual listo",
        body: "Tu informe de gastos de Marzo ya está disponible",
        date: "Ayer • 18:10",
        read: true,
        icon: "document",
      },
      {
        id: "3",
        title: "Recordatorio de presupuesto",
        body: "Has superado el 80% del presupuesto en Alimentación",
        date: "2 días",
        read: false,
        icon: "bell",
      },
    ],
    [],
  );

  const [items, setItems] = useState<NotificationItem[]>(initial);

  const toggleRead = (id: string) => {
    setItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, read: !it.read } : it)),
    );
  };

  const renderItem = ({ item }: { item: NotificationItem }) => {
    return (
      <Pressable
        onPress={() => toggleRead(item.id)}
        style={[
          styles.card,
          {
            backgroundColor: item.read
              ? isDark
                ? "#1f1f1f"
                : "#fafafa"
              : theme.cardBackground,
            shadowColor: theme.shadow,
          },
        ]}
      >
        <View style={styles.left}>
          <View
            style={[
              styles.iconWrap,
              {
                backgroundColor: isDark ? "rgba(255,255,255,0.03)" : "#eef9ff",
              },
            ]}
          >
            <IconSymbol
              name={
                (Platform.OS === "ios"
                  ? (item.icon as any)
                  : (item.icon as any)) ?? "bell"
              }
              size={18}
              color={theme.tint}
            />
          </View>
        </View>

        <View style={styles.middle}>
          <Text style={[styles.title, { color: theme.text }]} numberOfLines={1}>
            {item.title}
          </Text>
          <Text style={[styles.body, { color: theme.icon }]} numberOfLines={2}>
            {item.body}
          </Text>
        </View>

        <View style={styles.right}>
          <Text style={[styles.date, { color: theme.icon }]}>{item.date}</Text>
          <View
            style={[
              styles.dot,
              { backgroundColor: item.read ? "transparent" : theme.tint },
            ]}
          />
        </View>
      </Pressable>
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
            style={[styles.headerTitle, { color: theme.text }]}
          >
            Notificaciones
          </ThemedText>
          <ThemedText style={[styles.headerSubtitle, { color: theme.icon }]}>
            Últimas alertas y recordatorios
          </ThemedText>
        </View>

        <Pressable
          onPress={() => router.back()}
          style={[
            styles.closeBtn,
            {
              backgroundColor: isDark ? "#2a2a2a" : theme.cardBackground,
              shadowColor: theme.shadow,
            },
          ]}
          hitSlop={8}
        >
          <IconSymbol
            name={Platform.OS === "ios" ? ("xmark" as any) : ("close" as any)}
            size={18}
            color={theme.icon}
          />
        </Pressable>
      </View>

      <FlatList
        data={items}
        keyExtractor={(i) => i.id}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        contentContainerStyle={{ padding: 20, paddingBottom: 48 }}
      />

      <View style={styles.footer}>
        <Pressable
          onPress={() => {
            // mark all as read
            setItems((prev) => prev.map((it) => ({ ...it, read: true })));
          }}
          style={[styles.primaryBtn, { backgroundColor: theme.tint }]}
        >
          <ThemedText style={{ color: "#fff", fontWeight: "700" }}>
            Marcar todo como leído
          </ThemedText>
        </Pressable>
      </View>
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
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: "800",
  },
  headerSubtitle: {
    fontSize: 13,
    marginTop: 4,
  },
  closeBtn: {
    width: 42,
    height: 42,
    borderRadius: 21,
    alignItems: "center",
    justifyContent: "center",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    elevation: 6,
  },
  card: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    borderRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 4,
  },
  left: {
    width: 48,
    alignItems: "center",
    justifyContent: "center",
  },
  iconWrap: {
    width: 44,
    height: 44,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  middle: {
    flex: 1,
    paddingHorizontal: 8,
  },
  right: {
    width: 72,
    alignItems: "flex-end",
    justifyContent: "center",
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
  },
  body: {
    fontSize: 13,
    marginTop: 4,
  },
  date: {
    fontSize: 12,
    marginBottom: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 6,
  },
  footer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  primaryBtn: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
});
