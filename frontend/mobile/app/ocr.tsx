import React, { useState, useEffect } from "react";
import {
  View,
  StyleSheet,
  Pressable,
  Alert,
  Platform,
  ActivityIndicator,
  ScrollView,
  Image,
  TextInput,
  KeyboardAvoidingView,
} from "react-native";
import { useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as DocumentPicker from "expo-document-picker";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import api, { processFile, getCategories, getSources, SOURCE_EMOJIS } from "shared";
import { useAuth } from "@/contexts/AuthContext";

type Category = {
  id: number;
  name: string;
};

type Source = {
  id: number;
  name: string;
};

type EditableTransaction = {
  id: string;
  title: string;
  description: string;
  amount: string;
  transaction_type: "income" | "expense";
  date: string;
  category_id: number;
  source_id: number;
  state: string;
};

/**
 * OCR Screen - Real implementation
 * - Captures/selects images for document scanning
 * - Processes documents using backend OCR API
 * - Displays extracted text and confidence metrics
 */

// Document type options
const DOCUMENT_TYPES = [
  { value: "receipt", label: "Recibo", icon: "receipt" },
  { value: "invoice", label: "Factura", icon: "doc.text" },
  { value: "photo", label: "Foto", icon: "camera" },
  { value: "general", label: "General", icon: "doc" },
] as const;

export default function OcrScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [ocrResult, setOcrResult] = useState<any>(null);
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [selectedFileType, setSelectedFileType] = useState<
    "image" | "pdf" | null
  >(null);
  const [documentType, setDocumentType] = useState<string>("receipt");
  const [processingStep, setProcessingStep] = useState<string>("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [editableTransaction, setEditableTransaction] =
    useState<EditableTransaction | null>(null);

  useEffect(() => {
    getCategories().then((data) => setCategories(data));
    getSources().then((data) => setSources(data));
  }, []);

  const handleImagePicker = async (useCamera: boolean) => {
    try {
      let result;

      if (useCamera) {
        const permission = await ImagePicker.requestCameraPermissionsAsync();
        if (!permission.granted) {
          Alert.alert(
            "Permiso denegado",
            "Se requiere acceso a la cámara para escanear documentos",
          );
          return;
        }
        result = await ImagePicker.launchCameraAsync({
          mediaTypes: "images",
          aspect: [4, 3],
          quality: 0.8,
          allowsEditing: true,
        });
      } else {
        const permission =
          await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!permission.granted) {
          Alert.alert("Permiso denegado", "Se requiere acceso a la galería");
          return;
        }
        result = await ImagePicker.launchImageLibraryAsync({
          mediaTypes: "images",
          aspect: [4, 3],
          quality: 0.8,
          allowsEditing: true,
        });
      }

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        setSelectedFile(asset);
        setSelectedFileType("image");
        await processFileWithOCR(asset, "image");
      }
    } catch (error: any) {
      Alert.alert(
        "Error",
        `Error al seleccionar imagen: ${error.message || error}`,
      );
    }
  };

  const handleDocumentPicker = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: "application/pdf",
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        setSelectedFile(asset);
        setSelectedFileType("pdf");
        await processFileWithOCR(asset, "pdf");
      }
    } catch (error: any) {
      Alert.alert(
        "Error",
        `Error al seleccionar PDF: ${error.message || error}`,
      );
    }
  };

  const processFileWithOCR = async (
    fileAsset: any,
    fileType: "image" | "pdf",
  ) => {
    if (!user) {
      Alert.alert("Error", "Usuario no autenticado");
      return;
    }

    setLoading(true);
    setProcessingStep(
      fileType === "pdf" ? "Preparando PDF..." : "Preparando imagen...",
    );

    try {
      const timestamp = Date.now();
      const extension =
        fileAsset.uri.split(".").pop() || (fileType === "pdf" ? "pdf" : "jpg");
      const fileName =
        fileAsset.fileName ??
        fileAsset.name ??
        `scan_${timestamp}.${extension}`;
      const mimeType =
        fileType === "pdf"
          ? "application/pdf"
          : fileAsset.mimeType || `image/${extension}`;

      setProcessingStep(
        fileType === "pdf" ? "Subiendo PDF..." : "Subiendo imagen...",
      );

      const result = await processFile(
        {
          uri: fileAsset.uri,
          name: fileName,
          type: mimeType,
        },
        user.id,
        null,
        documentType,
      );

      setProcessingStep("Procesando OCR...");

      if (result.data) {
        setOcrResult(result.data);

        // Initialize editable transaction from OCR result
        const tx = result.data.transaction;
        const parsed = result.data.parsed_data;
        if (tx) {
          setEditableTransaction({
            id: tx.id,
            title: tx.title || parsed?.title || "",
            description: tx.description || parsed?.description || "",
            amount: String(tx.amount || parsed?.amount || 0),
            transaction_type:
              tx.transaction_type || parsed?.transaction_type || "expense",
            date: tx.date || parsed?.date || new Date().toISOString(),
            category_id:
              tx.category_id ||
              result.data.category?.id ||
              categories[0]?.id ||
              1,
            source_id:
              tx.source_id || result.data.source?.id || sources[0]?.id || 1,
            state: tx.state || "pending",
          });
        }
        setProcessingStep("");
      }
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        "Error al procesar la imagen";
      Alert.alert("Error de OCR", errorMessage);
      console.error("OCR Error:", error);
    } finally {
      setLoading(false);
      setProcessingStep("");
    }
  };

  const updateTransaction = async () => {
    if (!editableTransaction) return;

    setSaving(true);
    try {
      await api.patch(`/api/v1/transactions/${editableTransaction.id}`, {
        title: editableTransaction.title,
        description: editableTransaction.description,
        amount: parseFloat(editableTransaction.amount) || 0,
        transaction_type: editableTransaction.transaction_type,
        date: editableTransaction.date,
        category_id: editableTransaction.category_id,
        source_id: editableTransaction.source_id,
        state: "completed",
      });

      Alert.alert("Éxito", "Transacción actualizada y confirmada", [
        { text: "OK", onPress: () => router.push("/transactions") },
      ]);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Error al actualizar";
      Alert.alert("Error", errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const onStartScan = async () => {
    Alert.alert("Seleccionar origen", "¿Cómo desea escanear el documento?", [
      {
        text: "📷 Cámara",
        onPress: () => handleImagePicker(true),
      },
      {
        text: "🖼️ Galería",
        onPress: () => handleImagePicker(false),
      },
      {
        text: "📄 PDF",
        onPress: () => handleDocumentPicker(),
      },
      {
        text: "Cancelar",
        style: "cancel",
      },
    ]);
  };

  const resetScan = () => {
    setOcrResult(null);
    setSelectedFile(null);
    setSelectedFileType(null);
    setEditableTransaction(null);
    setProcessingStep("");
  };

  return (
    <ThemedView style={[styles.root, { backgroundColor: theme.background }]}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <ThemedText
              type="title"
              style={[styles.title, { color: theme.text }]}
            >
              OCR - Escanear documentos
            </ThemedText>
            <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
              Escanea recibos, facturas y documentos
            </ThemedText>
          </View>

          {!ocrResult ? (
            <>
              {/* Document Type Selector */}
              <View style={styles.typeSelector}>
                <ThemedText
                  style={[styles.typeSelectorLabel, { color: theme.text }]}
                >
                  Tipo de documento:
                </ThemedText>
                <View style={styles.typeButtons}>
                  {DOCUMENT_TYPES.map((type) => (
                    <Pressable
                      key={type.value}
                      onPress={() => setDocumentType(type.value)}
                      style={[
                        styles.typeButton,
                        {
                          backgroundColor:
                          documentType === type.value
                            ? theme.tint
                            : isDark
                              ? "#333"
                              : "#f0f0f0",
                      },
                    ]}
                  >
                    <ThemedText
                      style={[
                        styles.typeButtonText,
                        {
                          color:
                            documentType === type.value ? "#fff" : theme.text,
                        },
                      ]}
                    >
                      {type.label}
                    </ThemedText>
                  </Pressable>
                ))}
              </View>
            </View>

            {/* Preview file if selected */}
            {selectedFile && (
              <View style={styles.previewContainer}>
                {selectedFileType === "image" ? (
                  <Image
                    source={{ uri: selectedFile.uri }}
                    style={styles.previewImage}
                    resizeMode="contain"
                  />
                ) : (
                  <View style={styles.pdfPreview}>
                    <IconSymbol
                      name={"doc.fill" as any}
                      size={48}
                      color={theme.tint}
                    />
                    <ThemedText
                      style={[styles.pdfName, { color: theme.text }]}
                      numberOfLines={1}
                    >
                      {selectedFile.name || "documento.pdf"}
                    </ThemedText>
                  </View>
                )}
              </View>
            )}

            <View
              style={[
                styles.card,
                {
                  backgroundColor: isDark ? "#222" : theme.cardBackground,
                  shadowColor: theme.shadow,
                },
              ]}
            >
              <IconSymbol
                name={
                  Platform.OS === "ios"
                    ? ("doc.text.viewfinder" as any)
                    : ("document" as any)
                }
                size={48}
                color={theme.tint}
              />
              <ThemedText style={[styles.cardTitle, { color: theme.text }]}>
                Escaneo rápido
              </ThemedText>
              <ThemedText style={[styles.cardText, { color: theme.icon }]}>
                Usa la cámara, galería o sube un PDF para extraer datos
                automáticamente con IA.
              </ThemedText>

              {loading && processingStep && (
                <View style={styles.processingStatus}>
                  <ActivityIndicator color={theme.tint} size="small" />
                  <ThemedText
                    style={[styles.processingText, { color: theme.icon }]}
                  >
                    {processingStep}
                  </ThemedText>
                </View>
              )}

              <View style={styles.actions}>
                <Pressable
                  onPress={onStartScan}
                  disabled={loading}
                  style={({ pressed }) => [
                    styles.scanButton,
                    {
                      backgroundColor: pressed
                        ? theme.inputBackground
                        : theme.tint,
                      opacity: loading ? 0.6 : 1,
                    },
                  ]}
                >
                  {loading ? (
                    <ActivityIndicator
                      color={isDark ? "#1a1a1a" : "#fff"}
                      size="small"
                    />
                  ) : (
                    <ThemedText
                      style={[
                        styles.scanText,
                        { color: isDark ? "#1a1a1a" : "#fff" },
                      ]}
                    >
                      Iniciar escaneo
                    </ThemedText>
                  )}
                </Pressable>

                <Pressable
                  onPress={() => router.back()}
                  disabled={loading}
                  style={({ pressed }) => [
                    styles.backButton,
                    {
                      borderColor: pressed ? theme.inputBackground : theme.tint,
                      opacity: loading ? 0.6 : 1,
                    },
                  ]}
                >
                  <ThemedText style={[styles.backText, { color: theme.tint }]}>
                    Volver
                  </ThemedText>
                </Pressable>
              </View>
            </View>

            <View style={styles.note}>
              <ThemedText style={{ color: theme.icon, fontSize: 13 }}>
                Captura clara de documentos para mejores resultados. Soporta
                recibos, facturas, documentos y más.
              </ThemedText>
            </View>
          </>
        ) : (
          <>
            <View
              style={[
                styles.resultCard,
                {
                  backgroundColor: isDark ? "#222" : theme.cardBackground,
                  shadowColor: theme.shadow,
                },
              ]}
            >
              <View style={styles.resultHeader}>
                <IconSymbol
                  name={
                    Platform.OS === "ios"
                      ? ("checkmark.circle" as any)
                      : ("check" as any)
                  }
                  size={32}
                  color="#4CAF50"
                />
                <ThemedText style={[styles.resultTitle, { color: theme.text }]}>
                  Revisar y confirmar
                </ThemedText>
              </View>

              <View style={styles.confidenceSection}>
                <ThemedText
                  style={[styles.sectionLabel, { color: theme.text }]}
                >
                  Confianza OCR:{" "}
                  {Math.round(
                    ocrResult.extraction?.confidence ||
                      ocrResult.parsed_data?.confidence ||
                      0,
                  )}
                  %
                </ThemedText>
                <View
                  style={[
                    styles.confidenceBar,
                    { backgroundColor: theme.inputBackground },
                  ]}
                >
                  <View
                    style={[
                      styles.confidenceFill,
                      {
                        width: `${Math.min(
                          ocrResult.extraction?.confidence ||
                            ocrResult.parsed_data?.confidence ||
                            0,
                          100,
                        )}%`,
                        backgroundColor:
                          (ocrResult.extraction?.confidence ||
                            ocrResult.parsed_data?.confidence ||
                            0) >= 70
                            ? "#4CAF50"
                            : "#FFC107",
                      },
                    ]}
                  />
                </View>
              </View>

              <View
                style={[
                  styles.divider,
                  { backgroundColor: isDark ? "#444" : "#E0E0E0" },
                ]}
              />

              {editableTransaction && (
                <>
                  <ThemedText
                    style={[styles.sectionLabel, { color: theme.text }]}
                  >
                    Editar transacción:
                  </ThemedText>

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
                      value={editableTransaction.title}
                      onChangeText={(text) =>
                        setEditableTransaction({
                          ...editableTransaction,
                          title: text,
                        })
                      }
                      placeholder="Título de la transacción"
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
                      value={editableTransaction.description}
                      onChangeText={(text) =>
                        setEditableTransaction({
                          ...editableTransaction,
                          description: text,
                        })
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
                      value={editableTransaction.amount}
                      onChangeText={(text) =>
                        setEditableTransaction({
                          ...editableTransaction,
                          amount: text,
                        })
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
                          setEditableTransaction({
                            ...editableTransaction,
                            transaction_type: "expense",
                          })
                        }
                        style={[
                          styles.toggleButton,
                          {
                            backgroundColor:
                              editableTransaction.transaction_type === "expense"
                                ? "#ff6b6b"
                                : isDark
                                  ? "#333"
                                  : "#f0f0f0",
                          },
                        ]}
                      >
                        <ThemedText
                          style={{
                            color:
                              editableTransaction.transaction_type === "expense"
                                ? "#fff"
                                : theme.text,
                            fontWeight: "600",
                          }}
                        >
                          Gasto
                        </ThemedText>
                      </Pressable>
                      <Pressable
                        onPress={() =>
                          setEditableTransaction({
                            ...editableTransaction,
                            transaction_type: "income",
                          })
                        }
                        style={[
                          styles.toggleButton,
                          {
                            backgroundColor:
                              editableTransaction.transaction_type === "income"
                                ? "#2dd4bf"
                                : isDark
                                  ? "#333"
                                  : "#f0f0f0",
                          },
                        ]}
                      >
                        <ThemedText
                          style={{
                            color:
                              editableTransaction.transaction_type === "income"
                                ? "#fff"
                                : theme.text,
                            fontWeight: "600",
                          }}
                        >
                          Ingreso
                        </ThemedText>
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
                    <ScrollView
                      horizontal
                      showsHorizontalScrollIndicator={false}
                    >
                      <View style={styles.chipContainer}>
                        {categories.map((cat) => (
                          <Pressable
                            key={cat.id}
                            onPress={() =>
                              setEditableTransaction({
                                ...editableTransaction,
                                category_id: cat.id,
                              })
                            }
                            style={[
                              styles.chip,
                              {
                                backgroundColor:
                                  editableTransaction.category_id === cat.id
                                    ? theme.tint
                                    : isDark
                                      ? "#333"
                                      : "#f0f0f0",
                              },
                            ]}
                          >
                            <ThemedText
                              style={{
                                color:
                                  editableTransaction.category_id === cat.id
                                    ? "#fff"
                                    : theme.text,
                                fontSize: 13,
                              }}
                            >
                              {cat.name}
                            </ThemedText>
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
                    <ScrollView
                      horizontal
                      showsHorizontalScrollIndicator={false}
                    >
                      <View style={styles.chipContainer}>
                        {sources.map((src) => (
                          <Pressable
                            key={src.id}
                            onPress={() =>
                              setEditableTransaction({
                                ...editableTransaction,
                                source_id: src.id,
                              })
                            }
                            style={[
                              styles.chip,
                              {
                                backgroundColor:
                                  editableTransaction.source_id === src.id
                                    ? theme.tint
                                    : isDark
                                      ? "#333"
                                      : "#f0f0f0",
                              },
                            ]}
                          >
                             <ThemedText
                               style={{
                                 color:
                                   editableTransaction.source_id === src.id
                                     ? "#fff"
                                     : theme.text,
                                 fontSize: 13,
                               }}
                             >
                               {SOURCE_EMOJIS[src.name] || ''} {src.name}
                             </ThemedText>
                          </Pressable>
                        ))}
                      </View>
                    </ScrollView>
                  </View>
                </>
              )}

              <View
                style={[
                  styles.divider,
                  { backgroundColor: isDark ? "#444" : "#E0E0E0" },
                ]}
              />

              <View style={styles.actions}>
                <Pressable
                  onPress={updateTransaction}
                  disabled={saving}
                  style={({ pressed }) => [
                    styles.confirmButton,
                    {
                      backgroundColor: pressed ? "#1B8A6B" : "#22c55e",
                      opacity: saving ? 0.6 : 1,
                    },
                  ]}
                >
                  {saving ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <ThemedText style={[styles.scanText, { color: "#fff" }]}>
                      ✓ Confirmar transacción
                    </ThemedText>
                  )}
                </Pressable>
              </View>

              <View style={[styles.actions, { marginTop: 8 }]}>
                <Pressable
                  onPress={resetScan}
                  disabled={saving}
                  style={({ pressed }) => [
                    styles.backButton,
                    {
                      borderColor: pressed ? theme.inputBackground : theme.icon,
                      opacity: saving ? 0.6 : 1,
                    },
                  ]}
                >
                  <ThemedText style={[styles.backText, { color: theme.icon }]}>
                    Escanear otro
                  </ThemedText>
                </Pressable>

                <Pressable
                  onPress={() => router.push("/transactions")}
                  disabled={saving}
                  style={({ pressed }) => [
                    styles.backButton,
                    {
                      borderColor: pressed ? theme.inputBackground : theme.tint,
                      opacity: saving ? 0.6 : 1,
                    },
                  ]}
                >
                  <ThemedText style={[styles.backText, { color: theme.tint }]}>
                    Ver transacciones
                  </ThemedText>
                </Pressable>
              </View>
            </View>
          </>
        )}
      </ScrollView>
      </KeyboardAvoidingView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 28,
    paddingBottom: 10,
  },
  title: {
    fontSize: 22,
    fontWeight: "800",
  },
  subtitle: {
    marginTop: 6,
    fontSize: 13,
  },
  card: {
    margin: 20,
    borderRadius: 14,
    padding: 20,
    alignItems: "center",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 8,
  },
  resultCard: {
    margin: 20,
    borderRadius: 14,
    padding: 20,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 10,
    elevation: 8,
  },
  resultHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginLeft: 12,
  },
  cardTitle: {
    marginTop: 12,
    fontSize: 18,
    fontWeight: "700",
  },
  cardText: {
    marginTop: 6,
    fontSize: 14,
    textAlign: "center",
    maxWidth: 320,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: "600",
    marginTop: 12,
    marginBottom: 8,
  },
  confidenceSection: {
    marginBottom: 12,
  },
  confidenceBar: {
    height: 8,
    borderRadius: 4,
    overflow: "hidden",
    marginTop: 6,
  },
  confidenceFill: {
    height: "100%",
    borderRadius: 4,
  },
  divider: {
    height: 1,
    marginVertical: 16,
  },
  textBox: {
    borderRadius: 8,
    padding: 12,
    maxHeight: 200,
  },
  extractedText: {
    fontSize: 13,
    lineHeight: 20,
  },
  dataBox: {
    borderRadius: 8,
    padding: 12,
  },
  dataRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
  },
  dataLabel: {
    fontSize: 13,
    fontWeight: "600",
  },
  dataValue: {
    fontSize: 13,
    fontWeight: "500",
    maxWidth: "60%",
  },
  successBox: {
    flexDirection: "row",
    alignItems: "center",
    padding: 12,
    borderRadius: 8,
    marginVertical: 12,
  },
  actions: {
    marginTop: 18,
    width: "100%",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  scanButton: {
    flex: 1,
    marginRight: 8,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  scanText: {
    color: "#1a1a1a",
    fontWeight: "700",
  },
  backButton: {
    flex: 1,
    marginLeft: 8,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  backText: {
    fontWeight: "700",
  },
  note: {
    paddingHorizontal: 20,
    marginTop: 12,
  },
  typeSelector: {
    paddingHorizontal: 20,
    marginBottom: 10,
  },
  typeSelectorLabel: {
    fontSize: 14,
    fontWeight: "600",
    marginBottom: 10,
  },
  typeButtons: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  typeButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  typeButtonText: {
    fontSize: 13,
    fontWeight: "600",
  },
  previewContainer: {
    marginHorizontal: 20,
    marginBottom: 10,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#000",
  },
  previewImage: {
    width: "100%",
    height: 200,
  },
  pdfPreview: {
    width: "100%",
    height: 200,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#f0f4f8",
  },
  pdfName: {
    marginTop: 12,
    fontSize: 14,
    fontWeight: "600",
    maxWidth: "80%",
  },
  processingStatus: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 16,
    paddingVertical: 8,
  },
  processingText: {
    marginLeft: 10,
    fontSize: 13,
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
  confirmButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
});
