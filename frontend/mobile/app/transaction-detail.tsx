import { useState, useEffect } from "react";
import {
  View,
  StyleSheet,
  Text,
  ScrollView,
  Pressable,
  TextInput,
  Alert,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import api, { getCategories, getSources, SOURCE_EMOJIS } from "shared";

type Category = { id: number; name: string };
type Source = { id: number; name: string };

export default function TransactionDetailScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    id: string;
    title: string;
    description: string;
    amount: string;
    transaction_type: string;
    date: string;
    state: string;
    category_name: string;
    source_name: string;
    category_id: string;
    source_id: string;
    created_at: string;
    updated_at: string;
  }>();

  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";

  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sources, setSources] = useState<Source[]>([]);

  const [editData, setEditData] = useState({
    title: params.title || "",
    description: params.description || "",
    amount: params.amount || "0",
    transaction_type:
      (params.transaction_type as "income" | "expense") || "expense",
    category_id: parseInt(params.category_id || "1"),
    source_id: parseInt(params.source_id || "1"),
    state: params.state || "pending",
  });

  useEffect(() => {
    getCategories().then((data) => setCategories(data));
    getSources().then((data) => setSources(data));
  }, []);

  const isIncome = isEditing
    ? editData.transaction_type === "income"
    : params.transaction_type === "income";
  const amountColor = isIncome ? "#2dd4bf" : "#ff6b6b";
  const amount = parseFloat(isEditing ? editData.amount : params.amount || "0");

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "—";
    const date = new Date(dateStr);
    return date.toLocaleDateString("es-ES", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStateLabel = (state: string) => {
    switch (state) {
      case "pending":
        return { label: "Pendiente", color: "#f59e0b" };
      case "completed":
        return { label: "Completada", color: "#22c55e" };
      case "cancelled":
        return { label: "Cancelada", color: "#ef4444" };
      default:
        return { label: state, color: theme.icon };
    }
  };

  const stateInfo = getStateLabel(
    isEditing ? editData.state : params.state || "pending",
  );

  const getCategoryName = (id: number) => {
    const cat = categories.find((c) => c.id === id);
    return cat?.name || params.category_name || "Sin categoría";
  };

  const getSourceName = (id: number) => {
    const src = sources.find((s) => s.id === id);
    return src?.name || params.source_name || "Sin fuente";
  };

  const getSourceEmoji = (name: string) => {
    const lowerName = name.toLowerCase();
    return SOURCE_EMOJIS[lowerName] || "🏦";
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/api/v1/transactions/${params.id}`, {
        title: editData.title,
        description: editData.description,
        amount: parseFloat(editData.amount) || 0,
        transaction_type: editData.transaction_type,
        category_id: editData.category_id,
        source_id: editData.source_id,
        state: editData.state,
      });

      Alert.alert("Éxito", "Transacción actualizada", [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Error al actualizar";
      Alert.alert("Error", errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const DetailRow = ({
    icon,
    label,
    value,
    valueColor,
    emoji,
  }: {
    icon: string;
    label: string;
    value: string;
    valueColor?: string;
    emoji?: string;
  }) => (
    <View
      style={[
        styles.detailRow,
        {
          backgroundColor: theme.cardBackground,
          ...createShadow(0, 2, 4, theme.shadow, 2),
        },
      ]}
    >
      <View style={styles.detailLeft}>
        <View
          style={[
            styles.detailIcon,
            { backgroundColor: isDark ? "#333" : "#f0f4f8" },
          ]}
        >
          {emoji ? (
            <Text style={{ fontSize: 18 }}>{emoji}</Text>
          ) : (
            <IconSymbol name={icon as any} size={18} color={theme.tint} />
          )}
        </View>
        <Text style={[styles.detailLabel, { color: theme.icon }]}>{label}</Text>
      </View>
      <Text
        style={[styles.detailValue, { color: valueColor || theme.text }]}
        numberOfLines={2}
      >
        {value}
      </Text>
    </View>
  );

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <SafeAreaView style={{ flex: 1 }}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable
            onPress={() => router.back()}
            style={[
              styles.backButton,
              {
                backgroundColor: isDark ? "#333" : "#f0f4f8",
              },
            ]}
          >
            <IconSymbol
              name={"chevron.left" as any}
              size={20}
              color={theme.text}
            />
          </Pressable>
          <ThemedText
            type="title"
            style={[styles.headerTitle, { color: theme.text }]}
          >
            {isEditing ? "Editar" : "Detalle"}
          </ThemedText>
          <Pressable
            onPress={() => setIsEditing(!isEditing)}
            style={[
              styles.backButton,
              {
                backgroundColor: isEditing
                  ? theme.tint
                  : isDark
                    ? "#333"
                    : "#f0f4f8",
              },
            ]}
          >
            <IconSymbol
              name={isEditing ? ("xmark" as any) : ("pencil" as any)}
              size={18}
              color={isEditing ? "#fff" : theme.text}
            />
          </Pressable>
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Amount Card */}
          <View
            style={[
              styles.amountCard,
              {
                backgroundColor: isDark ? "#1a1a1a" : "#fff",
                ...createShadow(0, 6, 12, theme.shadow, 8),
              },
            ]}
          >
            <View
              style={[styles.typeIcon, { backgroundColor: amountColor + "22" }]}
            >
              <IconSymbol
                name={
                  isIncome
                    ? ("arrow.down.circle.fill" as any)
                    : ("arrow.up.circle.fill" as any)
                }
                size={32}
                color={amountColor}
              />
            </View>
            <Text style={[styles.amountLabel, { color: theme.icon }]}>
              {isIncome ? "Ingreso" : "Gasto"}
            </Text>
            <Text style={[styles.amountValue, { color: amountColor }]}>
              {isIncome ? "+" : "-"}${amount.toFixed(2)}
            </Text>
            <Pressable
              onPress={() => {
                if (isEditing) {
                  const states = ["pending", "completed", "cancelled"];
                  const currentIndex = states.indexOf(editData.state);
                  const nextState = states[(currentIndex + 1) % states.length];
                  setEditData({ ...editData, state: nextState });
                }
              }}
              style={[
                styles.stateBadge,
                { backgroundColor: stateInfo.color + "22" },
              ]}
            >
              <Text style={[styles.stateText, { color: stateInfo.color }]}>
                {stateInfo.label} {isEditing && "▾"}
              </Text>
            </Pressable>
          </View>

          {isEditing ? (
            <>
              {/* Editable Fields */}
              <View style={styles.editSection}>
                {/* Title */}
                <View style={styles.inputGroup}>
                  <ThemedText
                    style={[styles.inputLabel, { color: theme.icon }]}
                  >
                    Título
                  </ThemedText>
                  <TextInput
                    style={[
                      styles.input,
                      {
                        backgroundColor: isDark ? "#111" : "#f5f5f5",
                        color: theme.text,
                        borderColor: isDark ? "#444" : "#ddd",
                      },
                    ]}
                    value={editData.title}
                    onChangeText={(text) =>
                      setEditData({ ...editData, title: text })
                    }
                    placeholder="Título"
                    placeholderTextColor={theme.icon}
                  />
                </View>

                {/* Description */}
                <View style={styles.inputGroup}>
                  <ThemedText
                    style={[styles.inputLabel, { color: theme.icon }]}
                  >
                    Descripción
                  </ThemedText>
                  <TextInput
                    style={[
                      styles.input,
                      styles.textArea,
                      {
                        backgroundColor: isDark ? "#111" : "#f5f5f5",
                        color: theme.text,
                        borderColor: isDark ? "#444" : "#ddd",
                      },
                    ]}
                    value={editData.description}
                    onChangeText={(text) =>
                      setEditData({ ...editData, description: text })
                    }
                    placeholder="Descripción"
                    placeholderTextColor={theme.icon}
                    multiline
                    numberOfLines={3}
                  />
                </View>

                {/* Amount */}
                <View style={styles.inputGroup}>
                  <ThemedText
                    style={[styles.inputLabel, { color: theme.icon }]}
                  >
                    Monto ($)
                  </ThemedText>
                  <TextInput
                    style={[
                      styles.input,
                      {
                        backgroundColor: isDark ? "#111" : "#f5f5f5",
                        color: theme.text,
                        borderColor: isDark ? "#444" : "#ddd",
                      },
                    ]}
                    value={editData.amount}
                    onChangeText={(text) =>
                      setEditData({ ...editData, amount: text })
                    }
                    placeholder="0.00"
                    placeholderTextColor={theme.icon}
                    keyboardType="decimal-pad"
                  />
                </View>

                {/* Transaction Type */}
                <View style={styles.inputGroup}>
                  <ThemedText
                    style={[styles.inputLabel, { color: theme.icon }]}
                  >
                    Tipo
                  </ThemedText>
                  <View style={styles.typeToggle}>
                    <Pressable
                      onPress={() =>
                        setEditData({
                          ...editData,
                          transaction_type: "expense",
                        })
                      }
                      style={[
                        styles.toggleButton,
                        {
                          backgroundColor:
                            editData.transaction_type === "expense"
                              ? "#ff6b6b"
                              : isDark
                                ? "#333"
                                : "#f0f0f0",
                        },
                      ]}
                    >
                      <Text
                        style={{
                          color:
                            editData.transaction_type === "expense"
                              ? "#fff"
                              : theme.text,
                          fontWeight: "600",
                        }}
                      >
                        Gasto
                      </Text>
                    </Pressable>
                    <Pressable
                      onPress={() =>
                        setEditData({ ...editData, transaction_type: "income" })
                      }
                      style={[
                        styles.toggleButton,
                        {
                          backgroundColor:
                            editData.transaction_type === "income"
                              ? "#2dd4bf"
                              : isDark
                                ? "#333"
                                : "#f0f0f0",
                        },
                      ]}
                    >
                      <Text
                        style={{
                          color:
                            editData.transaction_type === "income"
                              ? "#fff"
                              : theme.text,
                          fontWeight: "600",
                        }}
                      >
                        Ingreso
                      </Text>
                    </Pressable>
                  </View>
                </View>

                {/* Category */}
                <View style={styles.inputGroup}>
                  <ThemedText
                    style={[styles.inputLabel, { color: theme.icon }]}
                  >
                    Categoría
                  </ThemedText>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.chipContainer}>
                      {categories.map((cat) => (
                        <Pressable
                          key={cat.id}
                          onPress={() =>
                            setEditData({ ...editData, category_id: cat.id })
                          }
                          style={[
                            styles.chip,
                            {
                              backgroundColor:
                                editData.category_id === cat.id
                                  ? theme.tint
                                  : isDark
                                    ? "#333"
                                    : "#f0f0f0",
                            },
                          ]}
                        >
                          <Text
                            style={{
                              color:
                                editData.category_id === cat.id
                                  ? "#fff"
                                  : theme.text,
                              fontSize: 13,
                            }}
                          >
                            {cat.name}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                {/* Source */}
                <View style={styles.inputGroup}>
                  <ThemedText
                    style={[styles.inputLabel, { color: theme.icon }]}
                  >
                    Fuente
                  </ThemedText>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                    <View style={styles.chipContainer}>
                      {sources.map((src) => (
                        <Pressable
                          key={src.id}
                          onPress={() =>
                            setEditData({ ...editData, source_id: src.id })
                          }
                          style={[
                            styles.chip,
                            {
                              backgroundColor:
                                editData.source_id === src.id
                                  ? theme.tint
                                  : isDark
                                    ? "#333"
                                    : "#f0f0f0",
                            },
                          ]}
                        >
                          <Text
                            style={{
                              color:
                                editData.source_id === src.id
                                  ? "#fff"
                                  : theme.text,
                              fontSize: 13,
                            }}
                          >
                            {src.name}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  </ScrollView>
                </View>

                {/* Save Button */}
                <Pressable
                  onPress={handleSave}
                  disabled={saving}
                  style={[
                    styles.saveButton,
                    {
                      backgroundColor: "#22c55e",
                      opacity: saving ? 0.6 : 1,
                    },
                  ]}
                >
                  {saving ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <Text style={styles.saveButtonText}>✓ Guardar cambios</Text>
                  )}
                </Pressable>
              </View>
            </>
          ) : (
            <>
              {/* Title & Description */}
              <View
                style={[
                  styles.infoCard,
                  {
                    backgroundColor: theme.cardBackground,
                    ...createShadow(0, 4, 8, theme.shadow, 4),
                  },
                ]}
              >
                <Text style={[styles.infoTitle, { color: theme.text }]}>
                  {params.title || "Sin título"}
                </Text>
                <Text style={[styles.infoDescription, { color: theme.icon }]}>
                  {params.description || "Sin descripción"}
                </Text>
              </View>

              {/* Details */}
              <View style={styles.detailsSection}>
                <Text style={[styles.sectionTitle, { color: theme.text }]}>
                  Información
                </Text>

                <DetailRow
                  icon="calendar"
                  label="Fecha"
                  value={formatDate(params.date || "")}
                />

                <DetailRow
                  icon="tag"
                  label="Categoría"
                  value={params.category_name || "Sin categoría"}
                />

                <DetailRow
                  icon="link"
                  label="Fuente"
                  value={params.source_name || "Sin fuente"}
                  emoji={getSourceEmoji(params.source_name || "")}
                />

                <DetailRow
                  icon="clock"
                  label="Creado"
                  value={formatDate(params.created_at || "")}
                />

                <DetailRow
                  icon="clock.arrow.circlepath"
                  label="Actualizado"
                  value={formatDate(params.updated_at || "")}
                />
              </View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  amountCard: {
    borderRadius: 20,
    padding: 24,
    alignItems: "center",
    marginBottom: 20,
  },
  typeIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  amountLabel: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 4,
  },
  amountValue: {
    fontSize: 36,
    fontWeight: "800",
    marginBottom: 12,
  },
  stateBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
  },
  stateText: {
    fontSize: 13,
    fontWeight: "700",
  },
  infoCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 8,
  },
  infoDescription: {
    fontSize: 14,
    lineHeight: 22,
  },
  detailsSection: {
    gap: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 4,
  },
  detailRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 14,
    borderRadius: 12,
  },
  detailLeft: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  detailIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: "500",
  },
  detailValue: {
    fontSize: 14,
    fontWeight: "600",
    textAlign: "right",
    maxWidth: "50%",
  },
  editSection: {
    gap: 16,
  },
  inputGroup: {
    marginBottom: 8,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 6,
  },
  input: {
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: "top",
  },
  typeToggle: {
    flexDirection: "row",
    gap: 10,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  chipContainer: {
    flexDirection: "row",
    gap: 8,
    paddingVertical: 4,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  saveButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 16,
  },
  saveButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
});
