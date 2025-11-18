import {
  View,
  StyleSheet,
  Pressable,
  ScrollView,
  Platform,
} from "react-native";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";

export default function ProfileScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  // Placeholder user data (replace with real store / API)
  const user = {
    name: "Usuario Ejemplo",
    email: "usuario@example.com",
  };

  return (
    <ThemedView style={[styles.root, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.headerRow}>
          <View>
            <ThemedText
              type="title"
              style={[styles.title, { color: theme.text }]}
            >
              Perfil
            </ThemedText>
            <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
              Información de la cuenta
            </ThemedText>
          </View>

          <Pressable
            onPress={() => router.back()}
            style={[
              styles.closeButton,
              {
                backgroundColor: isDark ? "#272727" : theme.cardBackground,
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

        <View
          style={[
            styles.card,
            {
              backgroundColor: theme.cardBackground,
              shadowColor: theme.shadow,
            },
          ]}
        >
          <View style={styles.avatarRow}>
            <View
              style={[
                styles.avatar,
                { backgroundColor: isDark ? "#333" : "#eef6ff" },
              ]}
            >
              <IconSymbol name={"person" as any} size={36} color={theme.tint} />
            </View>
            <View style={{ marginLeft: 12 }}>
              <ThemedText style={[styles.name, { color: theme.text }]}>
                {user.name}
              </ThemedText>
              <ThemedText style={[styles.email, { color: theme.icon }]}>
                {user.email}
              </ThemedText>
            </View>
          </View>

          <View style={styles.cardActions}>
            <Pressable
              style={[styles.actionRow, { borderColor: theme.inputBackground }]}
              onPress={() => router.push("/profile/edit" as any)}
            >
              <View style={styles.actionLeft}>
                <IconSymbol
                  name={"pencil" as any}
                  size={18}
                  color={theme.tint}
                />
                <ThemedText style={[styles.actionText, { color: theme.text }]}>
                  Editar perfil
                </ThemedText>
              </View>
              <IconSymbol
                name={
                  (Platform.OS === "ios"
                    ? "chevron.right"
                    : "chevron-right") as any
                }
                size={18}
                color={theme.icon}
              />
            </Pressable>

            <Pressable
              style={[styles.actionRow, { borderColor: theme.inputBackground }]}
              onPress={() => router.push("/profile/change-password" as any)}
            >
              <View style={styles.actionLeft}>
                <IconSymbol name={"lock" as any} size={18} color={theme.tint} />
                <ThemedText style={[styles.actionText, { color: theme.text }]}>
                  Cambiar contraseña
                </ThemedText>
              </View>
              <IconSymbol
                name={
                  (Platform.OS === "ios"
                    ? "chevron.right"
                    : "chevron-right") as any
                }
                size={18}
                color={theme.icon}
              />
            </Pressable>
          </View>
        </View>

        <View style={styles.section}>
          <ThemedText style={[styles.sectionTitle, { color: theme.text }]}>
            Actividad reciente
          </ThemedText>
          <ThemedText style={[styles.sectionSubtitle, { color: theme.icon }]}>
            (Placeholder) Últimas transacciones y acciones del asistente IA
          </ThemedText>
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
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 18,
  },
  closeButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    elevation: 6,
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
  },
  subtitle: {
    marginTop: 4,
    fontSize: 13,
  },
  card: {
    padding: 16,
    borderRadius: 14,
    marginBottom: 18,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 8,
  },
  avatarRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  name: {
    fontSize: 18,
    fontWeight: "800",
  },
  email: {
    fontSize: 13,
    marginTop: 2,
  },
  cardActions: {
    marginTop: 6,
  },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 10,
    borderWidth: 1,
    marginBottom: 10,
  },
  actionLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  actionText: {
    marginLeft: 10,
    fontSize: 15,
    fontWeight: "700",
  },
  section: {
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "800",
  },
  sectionSubtitle: {
    fontSize: 13,
    marginTop: 6,
  },
});
