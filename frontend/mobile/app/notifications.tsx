import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  StyleSheet,
  FlatList,
  Pressable,
  Text,
  Platform,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import { useNotificationContext } from "@/contexts/NotificationContext";
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
  type Notification as NotificationType,
} from "shared";

const ICON_MAP: Record<string, string> = {
  "arrow.up.circle": "arrow.up.circle.fill",
  "arrow.down.circle": "arrow.down.circle.fill",
  "exclamationmark.triangle": "exclamationmark.triangle.fill",
  "bell.badge": "bell.badge.fill",
  "lightbulb": "lightbulb.fill",
  "document": "doc.fill",
  "bell": "bell.fill",
};

export default function NotificationsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();
  const { refreshUnreadCount, syncReminders } = useNotificationContext();

  const [items, setItems] = useState<NotificationType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadNotifications = useCallback(async () => {
    if (!user?.id) return;
    try {
      const notifications = await getNotifications(user.id, { limit: 50 });
      setItems(notifications);
      // Sync reminders with local notifications when screen loads
      await syncReminders();
    } catch (error) {
      console.error("Error loading notifications:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [user?.id, syncReminders]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleRefresh = useCallback(() => {
    setIsRefreshing(true);
    loadNotifications();
  }, [loadNotifications]);

  const toggleRead = async (id: number, currentlyRead: boolean) => {
    if (!user?.id) return;
    
    // Optimistic update
    setItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, is_read: !currentlyRead } : it)),
    );

    if (!currentlyRead) {
      await markNotificationRead(user.id, id);
    }
  };

  const handleMarkAllRead = async () => {
    if (!user?.id) return;
    
    // Optimistic update
    setItems((prev) => prev.map((it) => ({ ...it, is_read: true })));
    
    await markAllNotificationsRead(user.id);
    await refreshUnreadCount();
  };

  const handleDelete = async (id: number) => {
    if (!user?.id) return;
    
    // Optimistic update
    setItems((prev) => prev.filter((it) => it.id !== id));
    
    await deleteNotification(user.id, id);
    await refreshUnreadCount();
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return `Hoy • ${date.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })}`;
    } else if (diffDays === 1) {
      return `Ayer • ${date.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" })}`;
    } else if (diffDays < 7) {
      return `${diffDays} días`;
    } else {
      return date.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
    }
  };

  const getIconColor = (type: string) => {
    switch (type) {
      case "transaction":
        return "#25d1b2";
      case "budget_alert":
        return "#ff6b6b";
      case "reminder":
        return "#7c4dff";
      case "report":
        return "#4dd0e1";
      case "tip":
        return "#ffb86b";
      case "goal":
        return "#8bc34a";
      default:
        return theme.tint;
    }
  };

  const renderItem = ({ item }: { item: NotificationType }) => {
    const iconName = ICON_MAP[item.icon] || item.icon || "bell.fill";
    const iconColor = getIconColor(item.notification_type);

    return (
      <Pressable
        onPress={() => toggleRead(item.id, item.is_read)}
        onLongPress={() => handleDelete(item.id)}
        style={[
          styles.card,
          {
            backgroundColor: item.is_read
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
                backgroundColor: isDark 
                  ? `${iconColor}22`
                  : `${iconColor}15`,
              },
            ]}
          >
            <IconSymbol
              name={iconName as any}
              size={18}
              color={iconColor}
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
          <Text style={[styles.date, { color: theme.icon }]}>
            {formatDate(item.created_at)}
          </Text>
          <View
            style={[
              styles.dot,
              { backgroundColor: item.is_read ? "transparent" : theme.tint },
            ]}
          />
        </View>
      </Pressable>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View
        style={[
          styles.emptyStateIcon,
          { backgroundColor: isDark ? "rgba(37, 209, 178, 0.16)" : "rgba(37, 209, 178, 0.08)" },
        ]}
      >
        <IconSymbol name={"bell.slash" as any} size={32} color={theme.icon} />
      </View>
      <ThemedText style={[styles.emptyStateTitle, { color: theme.text }]}>
        Sin notificaciones
      </ThemedText>
      <ThemedText style={[styles.emptyStateSubtitle, { color: theme.icon }]}>
        Aquí aparecerán tus alertas y recordatorios
      </ThemedText>
    </View>
  );

  if (!user) return null;

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
            {items.filter(i => !i.is_read).length} sin leer
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

      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.tint} />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(i) => i.id.toString()}
          renderItem={renderItem}
          ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
          contentContainerStyle={{ padding: 20, paddingBottom: 48, flexGrow: 1 }}
          ListEmptyComponent={renderEmptyState}
          refreshControl={
            <RefreshControl
              refreshing={isRefreshing}
              onRefresh={handleRefresh}
              tintColor={theme.tint}
            />
          }
        />
      )}

      {items.length > 0 && (
        <View style={styles.footer}>
          <Pressable
            onPress={handleMarkAllRead}
            style={[styles.primaryBtn, { backgroundColor: theme.tint }]}
          >
            <ThemedText style={{ color: isDark ? "#1a1a1a" : "#fff", fontWeight: "700" }}>
              Marcar todo como leído
            </ThemedText>
          </Pressable>
        </View>
      )}
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
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
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
  emptyState: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  emptyStateIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 8,
  },
  emptyStateSubtitle: {
    fontSize: 14,
    textAlign: "center",
  },
});
