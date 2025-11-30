/**
 * useNotifications Hook
 *
 * Manages notification permissions, listeners, and syncing with backend.
 */

import { useEffect, useRef, useCallback, useState } from "react";
import { AppState, AppStateStatus } from "react-native";
import * as Notifications from "expo-notifications";
import { useRouter } from "expo-router";
import { useAuth } from "@/contexts/AuthContext";
import {
  initializeNotifications,
  syncRemindersWithNotifications,
  setupNotificationResponseListener,
  setupNotificationReceivedListener,
  setBadgeCount,
} from "@/services/notifications";
import { getNotificationStats } from "shared";

export function useNotifications() {
  const { user } = useAuth();
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);
  const [isInitialized, setIsInitialized] = useState(false);
  const appState = useRef(AppState.currentState);
  const notificationListener = useRef<Notifications.EventSubscription | null>(
    null,
  );
  const responseListener = useRef<Notifications.EventSubscription | null>(null);

  // Handle notification tap
  const handleNotificationResponse = useCallback(
    (response: Notifications.NotificationResponse) => {
      const data = response.notification.request.content.data;

      if (data?.type === "reminder") {
        // Navigate to notifications screen
        router.push("/notifications");
      }
    },
    [router],
  );

  // Handle notification received while app is open
  const handleNotificationReceived = useCallback(
    (notification: Notifications.Notification) => {
      console.log("Notification received:", notification.request.content.title);
      // Refresh unread count
      if (user?.id) {
        refreshUnreadCount();
      }
    },
    [user?.id],
  );

  // Refresh unread notification count
  const refreshUnreadCount = useCallback(async () => {
    if (!user?.id) return;

    try {
      const stats = await getNotificationStats(user.id);
      if (stats) {
        setUnreadCount(stats.unread);
        await setBadgeCount(stats.unread);
      }
    } catch (error) {
      console.error("Error fetching notification stats:", error);
    }
  }, [user?.id]);

  // Sync reminders with local notifications
  const syncReminders = useCallback(async () => {
    if (!user?.id) return;

    try {
      await syncRemindersWithNotifications(user.id);
    } catch (error) {
      console.error("Error syncing reminders:", error);
    }
  }, [user?.id]);

  // Initialize notifications on mount
  useEffect(() => {
    async function init() {
      const success = await initializeNotifications();
      setIsInitialized(success);

      if (success && user?.id) {
        await syncReminders();
        await refreshUnreadCount();
      }
    }

    init();

    // Set up listeners
    notificationListener.current = setupNotificationReceivedListener(
      handleNotificationReceived,
    );
    responseListener.current = setupNotificationResponseListener(
      handleNotificationResponse,
    );

    return () => {
      notificationListener.current?.remove();
      responseListener.current?.remove();
    };
  }, [user?.id]);

  // Handle app state changes (sync when app comes to foreground)
  useEffect(() => {
    const subscription = AppState.addEventListener(
      "change",
      async (nextAppState: AppStateStatus) => {
        if (
          appState.current.match(/inactive|background/) &&
          nextAppState === "active" &&
          user?.id
        ) {
          // App has come to the foreground, sync reminders
          await syncReminders();
          await refreshUnreadCount();
        }
        appState.current = nextAppState;
      },
    );

    return () => {
      subscription.remove();
    };
  }, [user?.id, syncReminders, refreshUnreadCount]);

  return {
    isInitialized,
    unreadCount,
    refreshUnreadCount,
    syncReminders,
  };
}
