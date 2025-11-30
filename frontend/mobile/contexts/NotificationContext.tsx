/**
 * NotificationProvider
 * 
 * Initializes and manages notifications throughout the app.
 * Should be placed inside AuthProvider in the component tree.
 */

import React, { createContext, useContext, ReactNode } from "react";
import { useNotifications } from "@/hooks/use-notifications";

interface NotificationContextType {
  isInitialized: boolean;
  unreadCount: number;
  refreshUnreadCount: () => Promise<void>;
  syncReminders: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const notificationState = useNotifications();

  return (
    <NotificationContext.Provider value={notificationState}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotificationContext() {
  const context = useContext(NotificationContext);
  if (context === undefined) {
    throw new Error("useNotificationContext must be used within a NotificationProvider");
  }
  return context;
}
