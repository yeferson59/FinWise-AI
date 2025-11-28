import { useState } from "react";
import {
  View,
  StyleSheet,
  Switch,
  Pressable,
  Text,
  Platform,
  ScrollView,
} from "react-native";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

/**
 * Settings placeholder screen
 * - The screen adapts to the app theme using Colors + useColorScheme
 * - Contains toggles and quick actions that you can wire to real settings/state later
 * - Exported as default for route: /settings
 */

export default function SettingsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];

  // Local UI state for toggles (placeholder only)
  const [enableBiometrics, setEnableBiometrics] = useState(false);
  const [pushNotifications, setPushNotifications] = useState(true);
  const [useDarkThemeOverride, setUseDarkThemeOverride] = useState(false);

  return (
    <ThemedView style={[styles.root, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <ThemedText
            type="title"
            style={[styles.title, { color: theme.text }]}
          >
            Ajustes
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            Personaliza tu experiencia
          </ThemedText>
        </View>

        <View
          style={[
            styles.section,
            {
              backgroundColor: theme.cardBackground,
              shadowColor: theme.shadow,
            },
          ]}
        >
          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <IconSymbol
                name={
                  Platform.OS === "ios" ? ("person" as any) : ("person" as any)
                }
                size={20}
                color={theme.tint}
              />
              <Text style={[styles.label, { color: theme.text }]}>Cuenta</Text>
            </View>
            <Pressable onPress={() => router.push("/profile")}>
              <IconSymbol
                name={
                  Platform.OS === "ios"
                    ? ("chevron.right" as any)
                    : ("chevron-right" as any)
                }
                size={18}
                color={theme.icon}
              />
            </Pressable>
          </View>

          <View style={styles.divider} />

          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <IconSymbol
                name={
                  Platform.OS === "ios" ? ("shield" as any) : ("shield" as any)
                }
                size={20}
                color={theme.tint}
              />
              <Text style={[styles.label, { color: theme.text }]}>
                Biometría
              </Text>
            </View>
            <Switch
              value={enableBiometrics}
              onValueChange={(v) => setEnableBiometrics(v)}
              trackColor={{ true: theme.secondary, false: "#777" }}
            />
          </View>

          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <IconSymbol
                name={
                  Platform.OS === "ios"
                    ? ("bell" as any)
                    : ("notifications" as any)
                }
                size={20}
                color={theme.tint}
              />
              <Text style={[styles.label, { color: theme.text }]}>
                Notificaciones
              </Text>
            </View>
            <Switch
              value={pushNotifications}
              onValueChange={(v) => setPushNotifications(v)}
              trackColor={{ true: theme.secondary, false: "#777" }}
            />
          </View>
        </View>

        <View
          style={[
            styles.section,
            {
              backgroundColor: theme.cardBackground,
              shadowColor: theme.shadow,
            },
          ]}
        >
          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <IconSymbol
                name={
                  Platform.OS === "ios"
                    ? ("paintbrush" as any)
                    : ("palette" as any)
                }
                size={20}
                color={theme.tint}
              />
              <Text style={[styles.label, { color: theme.text }]}>
                Apariencia
              </Text>
            </View>
            <Switch
              value={useDarkThemeOverride}
              onValueChange={(v) => setUseDarkThemeOverride(v)}
              trackColor={{ true: theme.secondary, false: "#777" }}
            />
          </View>

          <View style={styles.divider} />

          <Pressable
            onPress={() => {}}
            style={[styles.row, { paddingVertical: 12 }]}
          >
            <View style={styles.rowLeft}>
              <IconSymbol
                name={
                  Platform.OS === "ios"
                    ? ("doc.text" as any)
                    : ("description" as any)
                }
                size={18}
                color={theme.tint}
              />
              <Text style={[styles.label, { color: theme.text }]}>
                Privacidad
              </Text>
            </View>
            <IconSymbol
              name={
                Platform.OS === "ios"
                  ? ("chevron.right" as any)
                  : ("chevron-right" as any)
              }
              size={18}
              color={theme.icon}
            />
          </Pressable>

          <Pressable
            onPress={() => {}}
            style={[styles.row, { paddingVertical: 12 }]}
          >
            <View style={styles.rowLeft}>
              <IconSymbol
                name={
                  Platform.OS === "ios"
                    ? ("questionmark.circle" as any)
                    : ("help" as any)
                }
                size={18}
                color={theme.tint}
              />
              <Text style={[styles.label, { color: theme.text }]}>
                Ayuda & Soporte
              </Text>
            </View>
            <IconSymbol
              name={
                Platform.OS === "ios"
                  ? ("chevron.right" as any)
                  : ("chevron-right" as any)
              }
              size={18}
              color={theme.icon}
            />
          </Pressable>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  container: {
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 10,
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
  },
  subtitle: {
    marginTop: 6,
    fontSize: 13,
  },
  section: {
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 6,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 8,
  },
  rowLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  label: {
    marginLeft: 12,
    fontSize: 16,
    fontWeight: "700",
  },
  divider: {
    height: 1,
    backgroundColor: "rgba(128,128,128,0.2)",
    marginVertical: 8,
  },
});
