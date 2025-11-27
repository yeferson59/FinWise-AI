import React, { useState } from "react";
import {
  View,
  StyleSheet,
  Pressable,
  Alert,
  Platform,
  ActivityIndicator,
  ScrollView,
  Image,
} from "react-native";
import { useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { processFile } from "shared";
import { useAuth } from "@/contexts/AuthContext";

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
  const [ocrResult, setOcrResult] = useState<any>(null);
  const [selectedImage, setSelectedImage] = useState<any>(null);
  const [documentType, setDocumentType] = useState<string>("receipt");
  const [processingStep, setProcessingStep] = useState<string>("");

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
          quality: 0.8, // Slightly reduced for faster upload
          allowsEditing: true, // Allow user to crop
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
        setSelectedImage(asset);
        await processImageWithOCR(asset);
      }
    } catch (error: any) {
      Alert.alert("Error", `Error al seleccionar imagen: ${error.message || error}`);
    }
  };

  const processImageWithOCR = async (imageAsset: any) => {
    if (!user) {
      Alert.alert("Error", "Usuario no autenticado");
      return;
    }

    setLoading(true);
    setProcessingStep("Preparando imagen...");
    
    try {
      // Generate filename with timestamp
      const timestamp = Date.now();
      const extension = imageAsset.uri.split(".").pop() || "jpg";
      const fileName = imageAsset.fileName ?? `scan_${timestamp}.${extension}`;

      setProcessingStep("Subiendo imagen...");

      const result = await processFile(
        {
          uri: imageAsset.uri,
          name: fileName,
          type: imageAsset.mimeType || `image/${extension}`,
        },
        user.id,
        null, // Let backend classify source
        documentType,
      );

      setProcessingStep("Procesando OCR...");

      if (result.data) {
        setOcrResult(result.data);
        setProcessingStep("");
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 
                          error.message || 
                          "Error al procesar la imagen";
      Alert.alert("Error de OCR", errorMessage);
      console.error("OCR Error:", error);
    } finally {
      setLoading(false);
      setProcessingStep("");
    }
  };

  const onStartScan = async () => {
    Alert.alert("Seleccionar origen", "¿Cómo desea escanear el documento?", [
      {
        text: "Cámara",
        onPress: () => handleImagePicker(true),
      },
      {
        text: "Galería",
        onPress: () => handleImagePicker(false),
      },
      {
        text: "Cancelar",
        style: "cancel",
      },
    ]);
  };

  const resetScan = () => {
    setOcrResult(null);
    setSelectedImage(null);
    setProcessingStep("");
  };

  return (
    <ThemedView style={[styles.root, { backgroundColor: theme.background }]}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
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
              <ThemedText style={[styles.typeSelectorLabel, { color: theme.text }]}>
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
                            : isDark ? "#333" : "#f0f0f0",
                      },
                    ]}
                  >
                    <ThemedText
                      style={[
                        styles.typeButtonText,
                        {
                          color: documentType === type.value ? "#fff" : theme.text,
                        },
                      ]}
                    >
                      {type.label}
                    </ThemedText>
                  </Pressable>
                ))}
              </View>
            </View>

            {/* Preview Image if selected */}
            {selectedImage && (
              <View style={styles.previewContainer}>
                <Image
                  source={{ uri: selectedImage.uri }}
                  style={styles.previewImage}
                  resizeMode="contain"
                />
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
                Usa la cámara para capturar recibos y extraer datos
                automáticamente con IA.
              </ThemedText>

              {loading && processingStep && (
                <View style={styles.processingStatus}>
                  <ActivityIndicator color={theme.tint} size="small" />
                  <ThemedText style={[styles.processingText, { color: theme.icon }]}>
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
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <ThemedText style={styles.scanText}>
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
                  Documento procesado
                </ThemedText>
              </View>

              <View style={styles.confidenceSection}>
                <ThemedText
                  style={[styles.sectionLabel, { color: theme.text }]}
                >
                  Confianza: {Math.round(ocrResult.extraction?.confidence || ocrResult.parsed_data?.confidence || 0)}%
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
                          ocrResult.extraction?.confidence || ocrResult.parsed_data?.confidence || 0,
                          100,
                        )}%`,
                        backgroundColor:
                          (ocrResult.extraction?.confidence || ocrResult.parsed_data?.confidence || 0) >= 70
                            ? "#4CAF50"
                            : "#FFC107",
                      },
                    ]}
                  />
                </View>
              </View>

              <View style={styles.divider} />

              <ThemedText style={[styles.sectionLabel, { color: theme.text }]}>
                Texto extraído:
              </ThemedText>
              <View
                style={[
                  styles.textBox,
                  { backgroundColor: isDark ? "#111" : "#f5f5f5" },
                ]}
              >
                <ThemedText
                  style={[
                    styles.extractedText,
                    {
                      color: theme.text,
                    },
                  ]}
                >
                  {ocrResult.extraction?.raw_text || "No se extrajo texto"}
                </ThemedText>
              </View>

              {ocrResult.parsed_data && (
                <>
                  <View style={styles.divider} />
                  <ThemedText
                    style={[styles.sectionLabel, { color: theme.text }]}
                  >
                    Datos extraídos:
                  </ThemedText>
                  <View
                    style={[
                      styles.dataBox,
                      { backgroundColor: isDark ? "#111" : "#f5f5f5" },
                    ]}
                  >
                    {ocrResult.parsed_data.title && (
                      <View style={styles.dataRow}>
                        <ThemedText
                          style={[styles.dataLabel, { color: theme.icon }]}
                        >
                          Título:
                        </ThemedText>
                        <ThemedText
                          style={[styles.dataValue, { color: theme.text, fontWeight: "600" }]}
                          numberOfLines={1}
                        >
                          {ocrResult.parsed_data.title}
                        </ThemedText>
                      </View>
                    )}
                    {(ocrResult.parsed_data.amount !== undefined && ocrResult.parsed_data.amount !== null) && (
                      <View style={styles.dataRow}>
                        <ThemedText
                          style={[styles.dataLabel, { color: theme.icon }]}
                        >
                          Monto:
                        </ThemedText>
                        <ThemedText
                          style={[styles.dataValue, { color: theme.text, fontWeight: "700", fontSize: 16 }]}
                        >
                          ${typeof ocrResult.parsed_data.amount === 'number' 
                            ? ocrResult.parsed_data.amount.toFixed(2) 
                            : ocrResult.parsed_data.amount}
                        </ThemedText>
                      </View>
                    )}
                    {ocrResult.parsed_data.date && (
                      <View style={styles.dataRow}>
                        <ThemedText
                          style={[styles.dataLabel, { color: theme.icon }]}
                        >
                          Fecha:
                        </ThemedText>
                        <ThemedText
                          style={[styles.dataValue, { color: theme.text }]}
                        >
                          {new Date(ocrResult.parsed_data.date).toLocaleDateString('es-ES', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                          })}
                        </ThemedText>
                      </View>
                    )}
                    {ocrResult.parsed_data.description && (
                      <View style={[styles.dataRow, { borderBottomWidth: 0 }]}>
                        <ThemedText
                          style={[styles.dataLabel, { color: theme.icon }]}
                        >
                          Descripción:
                        </ThemedText>
                        <ThemedText
                          style={[styles.dataValue, { color: theme.text }]}
                          numberOfLines={3}
                        >
                          {ocrResult.parsed_data.description}
                        </ThemedText>
                      </View>
                    )}
                  </View>
                </>
              )}

              {/* Category and Source */}
              {(ocrResult.category || ocrResult.source) && (
                <>
                  <View style={styles.divider} />
                  <ThemedText
                    style={[styles.sectionLabel, { color: theme.text }]}
                  >
                    Clasificación:
                  </ThemedText>
                  <View
                    style={[
                      styles.dataBox,
                      { backgroundColor: isDark ? "#111" : "#f5f5f5" },
                    ]}
                  >
                    {ocrResult.category && (
                      <View style={styles.dataRow}>
                        <ThemedText style={[styles.dataLabel, { color: theme.icon }]}>
                          Categoría:
                        </ThemedText>
                        <ThemedText style={[styles.dataValue, { color: theme.tint, fontWeight: "600" }]}>
                          {ocrResult.category.name}
                        </ThemedText>
                      </View>
                    )}
                    {ocrResult.source && (
                      <View style={[styles.dataRow, { borderBottomWidth: 0 }]}>
                        <ThemedText style={[styles.dataLabel, { color: theme.icon }]}>
                          Fuente:
                        </ThemedText>
                        <ThemedText style={[styles.dataValue, { color: theme.text }]}>
                          {ocrResult.source.name}
                        </ThemedText>
                      </View>
                    )}
                  </View>
                </>
              )}

              {ocrResult.transaction && (
                <>
                  <View style={styles.divider} />
                  <View
                    style={[styles.successBox, { backgroundColor: "#E8F5E9" }]}
                  >
                    <IconSymbol
                      name={
                        Platform.OS === "ios"
                          ? ("checkmark.circle.fill" as any)
                          : ("check_circle" as any)
                      }
                      size={20}
                      color="#4CAF50"
                    />
                    <ThemedText
                      style={{
                        color: "#2E7D32",
                        marginLeft: 8,
                        fontWeight: "600",
                      }}
                    >
                      Transacción creada exitosamente
                    </ThemedText>
                  </View>
                </>
              )}

              <View style={styles.actions}>
                <Pressable
                  onPress={resetScan}
                  style={({ pressed }) => [
                    styles.scanButton,
                    {
                      backgroundColor: pressed
                        ? theme.inputBackground
                        : theme.tint,
                    },
                  ]}
                >
                  <ThemedText style={styles.scanText}>
                    Escanear otro documento
                  </ThemedText>
                </Pressable>

                <Pressable
                  onPress={() => router.push("/transactions")}
                  style={({ pressed }) => [
                    styles.backButton,
                    {
                      borderColor: pressed ? theme.inputBackground : theme.tint,
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
    backgroundColor: "#E0E0E0",
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
    borderBottomColor: "#E0E0E0",
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
    color: "#fff",
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
});
