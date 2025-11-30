/**
 * Push Notifications Service
 * 
 * Handles local and push notifications for reminders and alerts.
 * Uses Expo Notifications API for scheduling and displaying notifications.
 */

import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { getNotifications, type Notification } from "shared";

const LAST_CHECK_KEY = "@finwise_last_reminder_check";
const SCHEDULED_NOTIFICATIONS_KEY = "@finwise_scheduled_notifications";

// Configure how notifications are handled when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

/**
 * Request notification permissions
 */
export async function requestNotificationPermissions(): Promise<boolean> {
  if (!Device.isDevice) {
    console.log("Push notifications only work on physical devices");
    return false;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.log("Notification permissions not granted");
    return false;
  }

  // Configure Android channel
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("reminders", {
      name: "Recordatorios",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: "#25d1b2",
      sound: "default",
    });

    await Notifications.setNotificationChannelAsync("transactions", {
      name: "Transacciones",
      importance: Notifications.AndroidImportance.DEFAULT,
      sound: "default",
    });

    await Notifications.setNotificationChannelAsync("alerts", {
      name: "Alertas",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 500, 250, 500],
      lightColor: "#ff6b6b",
      sound: "default",
    });
  }

  return true;
}

/**
 * Schedule a local notification for a reminder
 */
export async function scheduleReminderNotification(
  id: string,
  title: string,
  body: string,
  triggerDate: Date,
): Promise<string | null> {
  try {
    // Don't schedule if the date is in the past
    if (triggerDate <= new Date()) {
      console.log("Reminder date is in the past, skipping schedule");
      return null;
    }

    const notificationId = await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: "default",
        priority: Notifications.AndroidNotificationPriority.HIGH,
        data: { reminderId: id, type: "reminder" },
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DATE,
        date: triggerDate,
        channelId: "reminders",
      },
    });

    // Store scheduled notification ID for later cancellation if needed
    await storeScheduledNotification(id, notificationId);

    console.log(`Scheduled reminder notification: ${notificationId} for ${triggerDate}`);
    return notificationId;
  } catch (error) {
    console.error("Error scheduling notification:", error);
    return null;
  }
}

/**
 * Cancel a scheduled notification
 */
export async function cancelScheduledNotification(reminderId: string): Promise<void> {
  try {
    const scheduledNotifications = await getStoredScheduledNotifications();
    const notificationId = scheduledNotifications[reminderId];

    if (notificationId) {
      await Notifications.cancelScheduledNotificationAsync(notificationId);
      delete scheduledNotifications[reminderId];
      await AsyncStorage.setItem(
        SCHEDULED_NOTIFICATIONS_KEY,
        JSON.stringify(scheduledNotifications)
      );
      console.log(`Cancelled notification for reminder: ${reminderId}`);
    }
  } catch (error) {
    console.error("Error cancelling notification:", error);
  }
}

/**
 * Show an immediate notification
 */
export async function showImmediateNotification(
  title: string,
  body: string,
  data?: Record<string, unknown>,
): Promise<void> {
  try {
    await Notifications.scheduleNotificationAsync({
      content: {
        title,
        body,
        sound: "default",
        data,
      },
      trigger: null, // Show immediately
    });
  } catch (error) {
    console.error("Error showing notification:", error);
  }
}

/**
 * Check for due reminders and schedule their notifications
 */
export async function syncRemindersWithNotifications(userId: number): Promise<void> {
  try {
    // Get all unread notifications that are reminders
    const notifications = await getNotifications(userId, {
      notification_type: "reminder",
      unread_only: true,
      limit: 50,
    });

    const now = new Date();
    const scheduledNotifications = await getStoredScheduledNotifications();

    for (const notification of notifications) {
      if (notification.scheduled_at) {
        const scheduledDate = new Date(notification.scheduled_at);
        const notificationKey = notification.id.toString();

        // If already scheduled, skip
        if (scheduledNotifications[notificationKey]) {
          continue;
        }

        // If in the future, schedule it
        if (scheduledDate > now) {
          await scheduleReminderNotification(
            notificationKey,
            notification.title,
            notification.body,
            scheduledDate,
          );
        } else {
          // If it's past due and not read, show immediately
          await showImmediateNotification(
            notification.title,
            notification.body,
            { reminderId: notificationKey, type: "reminder" },
          );
        }
      }
    }

    // Update last check time
    await AsyncStorage.setItem(LAST_CHECK_KEY, now.toISOString());
  } catch (error) {
    console.error("Error syncing reminders:", error);
  }
}

/**
 * Get all scheduled notifications for debugging
 */
export async function getAllScheduledNotifications(): Promise<Notifications.NotificationRequest[]> {
  return Notifications.getAllScheduledNotificationsAsync();
}

/**
 * Cancel all scheduled notifications
 */
export async function cancelAllScheduledNotifications(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
  await AsyncStorage.removeItem(SCHEDULED_NOTIFICATIONS_KEY);
}

/**
 * Set up notification response listener
 */
export function setupNotificationResponseListener(
  onNotificationResponse: (response: Notifications.NotificationResponse) => void
): Notifications.EventSubscription {
  return Notifications.addNotificationResponseReceivedListener(onNotificationResponse);
}

/**
 * Set up notification received listener (when app is in foreground)
 */
export function setupNotificationReceivedListener(
  onNotificationReceived: (notification: Notifications.Notification) => void
): Notifications.EventSubscription {
  return Notifications.addNotificationReceivedListener(onNotificationReceived);
}

/**
 * Get badge count
 */
export async function getBadgeCount(): Promise<number> {
  return Notifications.getBadgeCountAsync();
}

/**
 * Set badge count
 */
export async function setBadgeCount(count: number): Promise<void> {
  await Notifications.setBadgeCountAsync(count);
}

// Helper functions for storing scheduled notification IDs

async function storeScheduledNotification(
  reminderId: string,
  notificationId: string
): Promise<void> {
  const scheduled = await getStoredScheduledNotifications();
  scheduled[reminderId] = notificationId;
  await AsyncStorage.setItem(SCHEDULED_NOTIFICATIONS_KEY, JSON.stringify(scheduled));
}

async function getStoredScheduledNotifications(): Promise<Record<string, string>> {
  try {
    const stored = await AsyncStorage.getItem(SCHEDULED_NOTIFICATIONS_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

/**
 * Initialize notification service
 */
export async function initializeNotifications(): Promise<boolean> {
  const hasPermission = await requestNotificationPermissions();
  
  if (hasPermission) {
    console.log("Notification service initialized");
  }
  
  return hasPermission;
}
