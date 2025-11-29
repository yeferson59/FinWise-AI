import { useState, useEffect } from "react";
import {
  View,
  FlatList,
  StyleSheet,
  Pressable,
  Text,
  Modal,
  TextInput,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import {
  getTransactions,
  getCategories,
  getSources,
  createTransaction,
} from "shared";

type Transaction = {
  id: string;
  user_id: number;
  category_id: number;
  source_id: number;
  title?: string;
  description: string;
  amount: number;
  transaction_type: "income" | "expense";
  date: string;
  state: string;
  updated_at: string;
  created_at: string;
};

type Category = {
  id: number;
  name: string;
};

type Source = {
  id: number;
  name: string;
};

export default function TransactionsScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isFormVisible, setIsFormVisible] = useState(false);
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    amount: "",
    transaction_type: "expense" as "income" | "expense",
    category_id: null as number | null,
    source_id: null as number | null,
    date: new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    if (user?.id) {
      getTransactions(user.id, 0, 50).then((data) => setTransactions(data));
      getCategories().then((data) => setCategories(data));
      getSources().then((data) => setSources(data));
    }
  }, [user?.id]);

  useEffect(() => {
    if (categories.length) {
      setFormData((prev) => ({
        ...prev,
        category_id: prev.category_id ?? categories[0].id,
      }));
    }
  }, [categories]);

  useEffect(() => {
    if (sources.length) {
      setFormData((prev) => ({
        ...prev,
        source_id: prev.source_id ?? sources[0].id,
      }));
    }
  }, [sources]);

  const getCategoryName = (id: number) => {
    const cat = categories.find((c) => c.id === id);
    return cat?.name || "Sin categoría";
  };

  const getSourceName = (id: number) => {
    const src = sources.find((s) => s.id === id);
    return src?.name || "Sin fuente";
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      amount: "",
      transaction_type: "expense",
      category_id: categories[0]?.id ?? null,
      source_id: sources[0]?.id ?? null,
      date: new Date().toISOString().slice(0, 10),
    });
    setFormError("");
  };

  const openForm = () => {
    resetForm();
    setIsFormVisible(true);
  };

  const closeForm = () => {
    if (!formSaving) {
      setIsFormVisible(false);
    }
  };

  const handleCreateTransaction = async () => {
    if (!user) return;
    if (!formData.amount || Number.isNaN(Number(formData.amount))) {
      setFormError("Ingresa un monto válido");
      return;
    }
    if (!formData.category_id || !formData.source_id) {
      setFormError("Selecciona categoría y fuente");
      return;
    }

    try {
      setFormSaving(true);
      setFormError("");
      const payload = {
        user_id: user.id,
        category_id: formData.category_id,
        source_id: formData.source_id,
        title: formData.title,
        description: formData.description || formData.title || "Sin descripción",
        amount: parseFloat(formData.amount),
        transaction_type: formData.transaction_type,
        date: new Date(formData.date || new Date().toISOString()).toISOString(),
      };

      const created = await createTransaction(payload as any);
      if (!created) {
        setFormError("No se pudo crear la transacción");
        return;
      }

      setTransactions((prev) => [created as Transaction, ...prev]);
      setIsFormVisible(false);
    } catch (error) {
      console.error("[Create Transaction]", error);
      setFormError("Ocurrió un error al guardar");
    } finally {
      setFormSaving(false);
    }
  };

  const onPressTransaction = (item: Transaction) => {
    router.push({
      pathname: "/transaction-detail",
      params: {
        id: item.id,
        title: item.title || "",
        description: item.description,
        amount: item.amount.toString(),
        transaction_type: item.transaction_type,
        date: item.date,
        state: item.state,
        category_name: getCategoryName(item.category_id),
        source_name: getSourceName(item.source_id),
        category_id: item.category_id.toString(),
        source_id: item.source_id.toString(),
        created_at: item.created_at,
        updated_at: item.updated_at,
      },
    });
  };

  const renderItem = ({ item }: { item: Transaction }) => {
    const isIncome = item.transaction_type === "income";
    const amountColor = isIncome ? "#2dd4bf" : "#ff6b6b";
    const formattedDate = item.date
      ? new Date(item.date).toLocaleDateString("es-ES", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : "";

    return (
      <Pressable
        onPress={() => onPressTransaction(item)}
        style={({ pressed }) => [
          styles.row,
          {
            backgroundColor: pressed
              ? isDark
                ? "#222"
                : "#f5f7fb"
              : theme.cardBackground,
            ...createShadow(0, 4, 8, theme.shadow, 3),
          },
        ]}
      >
        <View style={styles.left}>
          <View
            style={[
              styles.iconWrap,
              { backgroundColor: isDark ? "rgba(255,255,255,0.03)" : "#fff" },
            ]}
          >
            <IconSymbol
              name={
                isIncome
                  ? ("arrow.down.circle" as any)
                  : ("arrow.up.circle" as any)
              }
              size={18}
              color={amountColor}
            />
          </View>
          <View style={{ marginLeft: 12, flex: 1 }}>
            <Text
              style={[styles.title, { color: theme.text }]}
              numberOfLines={1}
              ellipsizeMode="tail"
            >
              {item.title || item.description || "Sin descripción"}
            </Text>
            <Text style={[styles.subtitle, { color: theme.icon }]}>
              {item.state === "pending" ? "Pendiente" : "Completada"}
            </Text>
          </View>
        </View>

        <View style={styles.right}>
          <Text style={[styles.dateText, { color: theme.icon }]}>
            {formattedDate}
          </Text>
          <Text style={[styles.amountText, { color: amountColor }]}>
            {isIncome ? "+" : "-"}${item.amount.toFixed(2)}
          </Text>
        </View>
      </Pressable>
    );
  };

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <SafeAreaView style={{ padding: 20 }}>
        <ThemedText type="title" style={[styles.header, { color: theme.text }]}>
          Transacciones
        </ThemedText>
        <ThemedText style={[styles.headerSub, { color: theme.icon }]}>
          Últimos movimientos
        </ThemedText>

        <FlatList
          data={transactions}
          keyExtractor={(t) => t.id}
          renderItem={renderItem}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
          contentContainerStyle={{ paddingTop: 16, paddingBottom: 60 }}
          showsVerticalScrollIndicator={false}
        />

        <Pressable
          onPress={openForm}
          style={({ pressed }) => [
            styles.addButton,
            { backgroundColor: pressed ? "#0b7285" : theme.tint },
          ]}
        >
          <IconSymbol
            name={"plus" as any}
            size={20}
            color={isDark ? "#1a1a1a" : "#fff"}
          />
          <ThemedText
            style={{ color: isDark ? "#1a1a1a" : "#fff", marginLeft: 8 }}
          >
            Nueva
          </ThemedText>
        </Pressable>
      </SafeAreaView>

      <Modal
        animationType="slide"
        transparent
        visible={isFormVisible}
        onRequestClose={closeForm}
      >
        <View style={styles.modalOverlay}>
          <View
            style={[styles.modalCard, { backgroundColor: theme.cardBackground }]}
          >
            <ThemedText style={[styles.modalTitle, { color: theme.text }]}>
              Nueva transacción
            </ThemedText>

            <ScrollView
              style={{ maxHeight: 420 }}
              showsVerticalScrollIndicator={false}
            >
              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.icon }]}>Título</Text>
                <TextInput
                  value={formData.title}
                  onChangeText={(title) => setFormData((prev) => ({ ...prev, title }))}
                  placeholder="Compra supermercado"
                  placeholderTextColor={theme.icon}
                  style={[
                    styles.input,
                    {
                      backgroundColor: isDark ? "#1f1f1f" : theme.inputBackground,
                      color: theme.text,
                    },
                  ]}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.icon }]}>Descripción</Text>
                <TextInput
                  value={formData.description}
                  onChangeText={(description) =>
                    setFormData((prev) => ({ ...prev, description }))
                  }
                  placeholder="Detalle opcional"
                  placeholderTextColor={theme.icon}
                  multiline
                  numberOfLines={3}
                  style={[
                    styles.textArea,
                    {
                      backgroundColor: isDark ? "#1f1f1f" : theme.inputBackground,
                      color: theme.text,
                    },
                  ]}
                />
              </View>

              <View style={styles.rowInputs}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.inputLabel, { color: theme.icon }]}>Monto</Text>
                  <TextInput
                    value={formData.amount}
                    onChangeText={(amount) => setFormData((prev) => ({ ...prev, amount }))}
                    keyboardType="decimal-pad"
                    placeholder="0.00"
                    placeholderTextColor={theme.icon}
                    style={[
                      styles.input,
                      {
                        backgroundColor: isDark ? "#1f1f1f" : theme.inputBackground,
                        color: theme.text,
                      },
                    ]}
                  />
                </View>
                <View style={{ width: 12 }} />
                <View style={{ flex: 1 }}>
                  <Text style={[styles.inputLabel, { color: theme.icon }]}>Fecha</Text>
                  <TextInput
                    value={formData.date}
                    onChangeText={(date) => setFormData((prev) => ({ ...prev, date }))}
                    placeholder="YYYY-MM-DD"
                    placeholderTextColor={theme.icon}
                    style={[
                      styles.input,
                      {
                        backgroundColor: isDark ? "#1f1f1f" : theme.inputBackground,
                        color: theme.text,
                      },
                    ]}
                  />
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.icon }]}>Tipo</Text>
                <View style={styles.toggleWrap}>
                  {["expense", "income"].map((type) => {
                    const active = formData.transaction_type === type;
                    return (
                      <Pressable
                        key={type}
                        onPress={() =>
                          setFormData((prev) => ({
                            ...prev,
                            transaction_type: type as "income" | "expense",
                          }))
                        }
                        style={[
                          styles.toggleButton,
                          {
                            backgroundColor: active
                              ? type === "income"
                                ? "#2dd4bf"
                                : "#ff6b6b"
                              : isDark
                                ? "#2a2a2a"
                                : theme.inputBackground,
                          },
                        ]}
                      >
                        <Text
                          style={{
                            color: active ? "#fff" : theme.text,
                            fontWeight: "600",
                          }}
                        >
                          {type === "income" ? "Ingreso" : "Gasto"}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.icon }]}>Categoría</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <View style={styles.chipRow}>
                    {categories.map((cat) => {
                      const active = formData.category_id === cat.id;
                      return (
                        <Pressable
                          key={cat.id}
                          onPress={() => setFormData((prev) => ({ ...prev, category_id: cat.id }))}
                          style={[
                            styles.chip,
                            {
                              backgroundColor: active
                                ? theme.tint
                                : isDark
                                  ? "#222"
                                  : "#f4f4f5",
                            },
                          ]}
                        >
                          <Text style={{ color: active ? "#fff" : theme.text }}>{cat.name}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                </ScrollView>
              </View>

              <View style={styles.inputGroup}>
                <Text style={[styles.inputLabel, { color: theme.icon }]}>Fuente</Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <View style={styles.chipRow}>
                    {sources.map((src) => {
                      const active = formData.source_id === src.id;
                      return (
                        <Pressable
                          key={src.id}
                          onPress={() => setFormData((prev) => ({ ...prev, source_id: src.id }))}
                          style={[
                            styles.chip,
                            {
                              backgroundColor: active
                                ? theme.tint
                                : isDark
                                  ? "#222"
                                  : "#f4f4f5",
                            },
                          ]}
                        >
                          <Text style={{ color: active ? "#fff" : theme.text }}>{src.name}</Text>
                        </Pressable>
                      );
                    })}
                  </View>
                </ScrollView>
              </View>
            </ScrollView>

            {formError ? (
              <Text style={styles.errorText}>{formError}</Text>
            ) : null}

            <View style={styles.modalActions}>
              <Pressable
                onPress={closeForm}
                disabled={formSaving}
                style={[styles.actionSecondary, { borderColor: theme.icon }]}
              >
                <Text style={{ color: theme.icon, fontWeight: "700" }}>Cancelar</Text>
              </Pressable>
              <Pressable
                onPress={handleCreateTransaction}
                disabled={formSaving}
                style={[
                  styles.actionPrimary,
                  { backgroundColor: formSaving ? "#9ca3af" : theme.tint },
                ]}
              >
                {formSaving ? (
                  <ActivityIndicator color={isDark ? "#1a1a1a" : "#fff"} />
                ) : (
                  <Text style={{ color: isDark ? "#1a1a1a" : "#fff", fontWeight: "700" }}>
                    Guardar
                  </Text>
                )}
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    fontSize: 26,
    fontWeight: "800",
    marginBottom: 2,
  },
  headerSub: {
    fontSize: 13,
    marginBottom: 12,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    ...createShadow(0, 4, 8, "rgba(0,0,0,0.06)", 3),
    justifyContent: "space-between",
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    marginRight: 12,
  },
  iconWrap: {
    width: 46,
    height: 46,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 13,
    marginTop: 4,
  },
  right: {
    alignItems: "flex-end",
    marginLeft: 12,
    width: 110,
  },
  dateText: {
    fontSize: 12,
  },
  amountText: {
    fontSize: 16,
    fontWeight: "800",
    marginTop: 6,
  },
  addButton: {
    position: "absolute",
    right: 28,
    bottom: 24,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.18)", 6),
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "center",
    paddingHorizontal: 20,
  },
  modalCard: {
    borderRadius: 18,
    padding: 20,
    maxHeight: "90%",
    ...createShadow(0, 12, 24, "rgba(0,0,0,0.3)", 12),
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: "800",
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 14,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 6,
  },
  input: {
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
  },
  textArea: {
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    minHeight: 80,
    textAlignVertical: "top",
  },
  rowInputs: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 14,
  },
  toggleWrap: {
    flexDirection: "row",
    gap: 12,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
  },
  chipRow: {
    flexDirection: "row",
    gap: 10,
    paddingVertical: 4,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
  },
  errorText: {
    color: "#ef4444",
    fontWeight: "600",
    textAlign: "center",
    marginBottom: 12,
  },
  modalActions: {
    flexDirection: "row",
    gap: 12,
  },
  actionSecondary: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  actionPrimary: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
});
