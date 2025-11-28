import { useState, useEffect } from "react";
import {
  View,
  StyleSheet,
  FlatList,
  Pressable,
  Text,
  Modal,
  TextInput,
  Alert,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import { getCategories, createCategory, updateCategory, deleteCategory } from "shared";

// Colores predefinidos para categorías
const CATEGORY_COLORS = [
  "#ff6b6b",
  "#4dd0e1",
  "#8bc34a",
  "#ffb86b",
  "#7c4dff",
  "#e91e63",
  "#00bcd4",
  "#4caf50",
  "#ff9800",
  "#9c27b0",
  "#f44336",
  "#03a9f4",
  "#cddc39",
  "#ff5722",
  "#673ab7",
];

// Emojis por nombre de categoría (mapeo común)
const CATEGORY_EMOJIS: Record<string, string> = {
  alimentación: "🍕",
  comida: "🍕",
  food: "🍕",
  transporte: "🚗",
  transport: "🚗",
  hogar: "🏠",
  home: "🏠",
  entretenimiento: "🎬",
  entertainment: "🎬",
  salud: "💊",
  health: "💊",
  educación: "📚",
  education: "📚",
  compras: "🛒",
  shopping: "🛒",
  servicios: "🔧",
  services: "🔧",
  otros: "📦",
  other: "📦",
  general: "📦",
};

type Category = {
  id: number;
  name: string;
  description?: string | null;
  is_default: boolean;
  user_id?: number | null;
  updated_at: string;
  created_at: string;
};

export default function CategoriesScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [newCategoryDescription, setNewCategoryDescription] = useState("");
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  const loadCategories = () => {
    getCategories().then((data) => setCategories(data));
  };

  useEffect(() => {
    loadCategories();
  }, []);

  const openCategoryDetail = (category: Category) => {
    setSelectedCategory(category);
    setEditName(category.name);
    setEditDescription(category.description || "");
    setIsEditing(false);
    setDetailModalVisible(true);
  };

  const handleUpdateCategory = async () => {
    if (!selectedCategory || !editName.trim()) {
      Alert.alert("Error", "El nombre es requerido");
      return;
    }

    setSaving(true);
    try {
      await updateCategory(
        selectedCategory.id,
        editName.trim(),
        editDescription.trim() || undefined
      );
      setDetailModalVisible(false);
      loadCategories();
      Alert.alert("Éxito", "Categoría actualizada");
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || "Error al actualizar";
      Alert.alert("Error", errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) {
      Alert.alert("Error", "El nombre de la categoría es requerido");
      return;
    }

    setSaving(true);
    try {
      await createCategory(
        newCategoryName.trim(),
        newCategoryDescription.trim() || undefined,
        user?.id
      );
      setModalVisible(false);
      setNewCategoryName("");
      setNewCategoryDescription("");
      loadCategories();
      Alert.alert("Éxito", "Categoría creada correctamente");
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || "Error al crear categoría";
      Alert.alert("Error", errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCategory = (item: Category) => {
    if (item.is_default) {
      Alert.alert("No permitido", "No puedes eliminar categorías predeterminadas");
      return;
    }

    Alert.alert(
      "Eliminar categoría",
      `¿Estás seguro de eliminar "${item.name}"?`,
      [
        { text: "Cancelar", style: "cancel" },
        {
          text: "Eliminar",
          style: "destructive",
          onPress: async () => {
            try {
              await deleteCategory(item.id);
              loadCategories();
              Alert.alert("Éxito", "Categoría eliminada");
            } catch (error: any) {
              const errorMessage = error.response?.data?.detail || error.message || "Error al eliminar";
              Alert.alert("Error", errorMessage);
            }
          },
        },
      ]
    );
  };

  const getCategoryColor = (index: number) => {
    return CATEGORY_COLORS[index % CATEGORY_COLORS.length];
  };

  const getCategoryEmoji = (name: string) => {
    const lowerName = name.toLowerCase();
    return CATEGORY_EMOJIS[lowerName] || "🏷️";
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleDateString("es-ES", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  };

  const renderItem = ({ item, index }: { item: Category; index: number }) => {
    const color = getCategoryColor(index);
    const emoji = getCategoryEmoji(item.name);

    return (
      <Pressable
        style={[
          styles.row,
          {
            backgroundColor: theme.cardBackground,
            ...createShadow(0, 6, 8, theme.shadow, 4),
          },
        ]}
        onPress={() => openCategoryDetail(item)}
        onLongPress={() => handleDeleteCategory(item)}
      >
        <View style={styles.left}>
          <View style={[styles.iconWrap, { backgroundColor: color + "22" }]}>
            <Text style={{ fontSize: 18 }}>{emoji}</Text>
          </View>
          <View style={{ marginLeft: 12, flex: 1 }}>
            <ThemedText
              style={[styles.title, { color: theme.text }]}
              numberOfLines={1}
            >
              {item.name}
            </ThemedText>
            <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
              {item.description ||
                (item.is_default
                  ? "Categoría predeterminada"
                  : "Categoría personalizada")}
            </ThemedText>
          </View>
        </View>

        <View style={styles.right}>
          <View style={[styles.badge, { backgroundColor: color + "22" }]}>
            <Text style={{ color: color, fontSize: 12, fontWeight: "600" }}>
              {item.is_default ? "Default" : "Custom"}
            </Text>
          </View>
        </View>
      </Pressable>
    );
  };

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <View style={styles.header}>
        <ThemedText
          type="title"
          style={[styles.headerTitle, { color: theme.text }]}
        >
          Categorías
        </ThemedText>
        <ThemedText style={[styles.headerSubtitle, { color: theme.icon }]}>
          Mantén presionado para eliminar personalizadas
        </ThemedText>
      </View>

      <FlatList
        data={categories}
        keyExtractor={(c) => c.id.toString()}
        contentContainerStyle={{ padding: 20, paddingBottom: 48 }}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        showsVerticalScrollIndicator={false}
      />

      <Pressable
        onPress={() => setModalVisible(true)}
        style={[
          styles.fab,
          {
            backgroundColor: theme.tint,
            ...createShadow(0, 6, 8, theme.shadow, 8),
          },
        ]}
      >
        <IconSymbol
          name={"plus" as any}
          size={20}
          color={isDark ? "#1a1a1a" : "#fff"}
        />
      </Pressable>

      {/* Modal para crear categoría */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.modalContent,
              { backgroundColor: isDark ? "#1a1a1a" : "#fff" },
            ]}
          >
            <View style={styles.modalHeader}>
              <ThemedText style={[styles.modalTitle, { color: theme.text }]}>
                Nueva categoría
              </ThemedText>
              <Pressable onPress={() => setModalVisible(false)}>
                <IconSymbol
                  name={"xmark.circle.fill" as any}
                  size={28}
                  color={theme.icon}
                />
              </Pressable>
            </View>

            <View style={styles.inputGroup}>
              <ThemedText style={[styles.inputLabel, { color: theme.icon }]}>
                Nombre *
              </ThemedText>
              <TextInput
                style={[
                  styles.input,
                  {
                    backgroundColor: isDark ? "#333" : "#f5f5f5",
                    color: theme.text,
                    borderColor: isDark ? "#444" : "#ddd",
                  },
                ]}
                value={newCategoryName}
                onChangeText={setNewCategoryName}
                placeholder="Ej: Viajes, Mascotas, Gym..."
                placeholderTextColor={theme.icon}
              />
            </View>

            <View style={styles.inputGroup}>
              <ThemedText style={[styles.inputLabel, { color: theme.icon }]}>
                Descripción (opcional)
              </ThemedText>
              <TextInput
                style={[
                  styles.input,
                  styles.textArea,
                  {
                    backgroundColor: isDark ? "#333" : "#f5f5f5",
                    color: theme.text,
                    borderColor: isDark ? "#444" : "#ddd",
                  },
                ]}
                value={newCategoryDescription}
                onChangeText={setNewCategoryDescription}
                placeholder="Descripción de la categoría"
                placeholderTextColor={theme.icon}
                multiline
                numberOfLines={3}
              />
            </View>

            <Pressable
              onPress={handleCreateCategory}
              disabled={saving}
              style={[
                styles.createButton,
                {
                  backgroundColor: "#22c55e",
                  opacity: saving ? 0.6 : 1,
                },
              ]}
            >
              {saving ? (
                <ActivityIndicator color="#fff" size="small" />
              ) : (
                <Text style={styles.createButtonText}>Crear categoría</Text>
              )}
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* Modal de detalle/edición */}
      <Modal
        visible={detailModalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setDetailModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View
            style={[
              styles.modalContent,
              { backgroundColor: isDark ? "#1a1a1a" : "#fff" },
            ]}
          >
            <View style={styles.modalHeader}>
              <ThemedText style={[styles.modalTitle, { color: theme.text }]}>
                {isEditing ? "Editar categoría" : "Detalle de categoría"}
              </ThemedText>
              <Pressable onPress={() => setDetailModalVisible(false)}>
                <IconSymbol
                  name={"xmark.circle.fill" as any}
                  size={28}
                  color={theme.icon}
                />
              </Pressable>
            </View>

            {selectedCategory && (
              <ScrollView showsVerticalScrollIndicator={false}>
                {/* Emoji y badge */}
                <View style={styles.detailHeader}>
                  <View
                    style={[
                      styles.detailEmoji,
                      { backgroundColor: getCategoryColor(categories.indexOf(selectedCategory)) + "22" },
                    ]}
                  >
                    <Text style={{ fontSize: 32 }}>
                      {getCategoryEmoji(selectedCategory.name)}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.detailBadge,
                      {
                        backgroundColor: selectedCategory.is_default
                          ? "#22c55e22"
                          : "#7c4dff22",
                      },
                    ]}
                  >
                    <Text
                      style={{
                        color: selectedCategory.is_default ? "#22c55e" : "#7c4dff",
                        fontWeight: "600",
                        fontSize: 13,
                      }}
                    >
                      {selectedCategory.is_default ? "Predeterminada" : "Personalizada"}
                    </Text>
                  </View>
                </View>

                {isEditing ? (
                  <>
                    {/* Campos editables */}
                    <View style={styles.inputGroup}>
                      <ThemedText style={[styles.inputLabel, { color: theme.icon }]}>
                        Nombre
                      </ThemedText>
                      <TextInput
                        style={[
                          styles.input,
                          {
                            backgroundColor: isDark ? "#333" : "#f5f5f5",
                            color: theme.text,
                            borderColor: isDark ? "#444" : "#ddd",
                          },
                        ]}
                        value={editName}
                        onChangeText={setEditName}
                        placeholder="Nombre de la categoría"
                        placeholderTextColor={theme.icon}
                      />
                    </View>

                    <View style={styles.inputGroup}>
                      <ThemedText style={[styles.inputLabel, { color: theme.icon }]}>
                        Descripción
                      </ThemedText>
                      <TextInput
                        style={[
                          styles.input,
                          styles.textArea,
                          {
                            backgroundColor: isDark ? "#333" : "#f5f5f5",
                            color: theme.text,
                            borderColor: isDark ? "#444" : "#ddd",
                          },
                        ]}
                        value={editDescription}
                        onChangeText={setEditDescription}
                        placeholder="Descripción"
                        placeholderTextColor={theme.icon}
                        multiline
                        numberOfLines={3}
                      />
                    </View>

                    <View style={styles.editActions}>
                      <Pressable
                        onPress={() => setIsEditing(false)}
                        style={[styles.cancelButton, { borderColor: theme.icon }]}
                      >
                        <Text style={[styles.cancelButtonText, { color: theme.icon }]}>
                          Cancelar
                        </Text>
                      </Pressable>
                      <Pressable
                        onPress={handleUpdateCategory}
                        disabled={saving}
                        style={[
                          styles.saveButton,
                          { backgroundColor: "#22c55e", opacity: saving ? 0.6 : 1 },
                        ]}
                      >
                        {saving ? (
                          <ActivityIndicator color="#fff" size="small" />
                        ) : (
                          <Text style={styles.saveButtonText}>Guardar</Text>
                        )}
                      </Pressable>
                    </View>
                  </>
                ) : (
                  <>
                    {/* Vista de solo lectura */}
                    <View style={styles.detailRow}>
                      <ThemedText style={[styles.detailLabel, { color: theme.icon }]}>
                        Nombre
                      </ThemedText>
                      <ThemedText style={[styles.detailValue, { color: theme.text }]}>
                        {selectedCategory.name}
                      </ThemedText>
                    </View>

                    <View style={styles.detailRow}>
                      <ThemedText style={[styles.detailLabel, { color: theme.icon }]}>
                        Descripción
                      </ThemedText>
                      <ThemedText style={[styles.detailValue, { color: theme.text }]}>
                        {selectedCategory.description || "Sin descripción"}
                      </ThemedText>
                    </View>

                    <View style={styles.detailRow}>
                      <ThemedText style={[styles.detailLabel, { color: theme.icon }]}>
                        Creada
                      </ThemedText>
                      <ThemedText style={[styles.detailValue, { color: theme.text }]}>
                        {formatDate(selectedCategory.created_at)}
                      </ThemedText>
                    </View>

                    <View style={styles.detailRow}>
                      <ThemedText style={[styles.detailLabel, { color: theme.icon }]}>
                        Actualizada
                      </ThemedText>
                      <ThemedText style={[styles.detailValue, { color: theme.text }]}>
                        {formatDate(selectedCategory.updated_at)}
                      </ThemedText>
                    </View>

                    {!selectedCategory.is_default && (
                      <Pressable
                        onPress={() => setIsEditing(true)}
                        style={[styles.editButton, { backgroundColor: theme.tint }]}
                      >
                        <IconSymbol name={"pencil" as any} size={16} color="#fff" />
                        <Text style={styles.editButtonText}>Editar categoría</Text>
                      </Pressable>
                    )}
                  </>
                )}
              </ScrollView>
            )}
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
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 8,
  },
  headerTitle: {
    fontSize: 26,
    fontWeight: "800",
  },
  headerSubtitle: {
    fontSize: 13,
    marginTop: 6,
  },
  row: {
    padding: 14,
    borderRadius: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.06)", 4),
  },
  left: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 13,
    marginTop: 2,
  },
  right: {
    alignItems: "flex-end",
    marginLeft: 12,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  fab: {
    position: "absolute",
    right: 18,
    bottom: 26,
    width: 52,
    height: 52,
    borderRadius: 26,
    alignItems: "center",
    justifyContent: "center",
    ...createShadow(0, 6, 8, "rgba(0,0,0,0.18)", 8),
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  modalContent: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 24,
    paddingBottom: 40,
  },
  modalHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 24,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: "700",
  },
  inputGroup: {
    marginBottom: 16,
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
  createButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 8,
  },
  createButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
  detailHeader: {
    alignItems: "center",
    marginBottom: 24,
  },
  detailEmoji: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  detailBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
  },
  detailRow: {
    marginBottom: 16,
  },
  detailLabel: {
    fontSize: 13,
    fontWeight: "600",
    marginBottom: 4,
  },
  detailValue: {
    fontSize: 16,
  },
  editButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 16,
    gap: 8,
  },
  editButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 15,
  },
  editActions: {
    flexDirection: "row",
    gap: 12,
    marginTop: 16,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  cancelButtonText: {
    fontWeight: "700",
    fontSize: 15,
  },
  saveButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  saveButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 15,
  },
});
