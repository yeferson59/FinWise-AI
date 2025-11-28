import React, { useState, useEffect } from "react";
import {
  View,
  StyleSheet,
  Pressable,
  Alert,
  Platform,
  ActivityIndicator,
  ScrollView,
  TextInput,
} from "react-native";
import { useRouter } from "expo-router";
import { AudioModule, RecordingPresets, useAudioRecorder } from "expo-audio";
import { File, Paths } from "expo-file-system";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { Colors } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import api, { processFile, getCategories, getSources } from "shared";
import { useAuth } from "@/contexts/AuthContext";

type Category = { id: number; name: string };
type Source = { id: number; name: string };

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

export default function AudioTransactionScreen() {
  const router = useRouter();
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();

  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [processingStep, setProcessingStep] = useState("");
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [editableTransaction, setEditableTransaction] =
    useState<EditableTransaction | null>(null);

  useEffect(() => {
    getCategories().then((data) => setCategories(data));
    getSources().then((data) => setSources(data));
  }, []);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const configureAudioSession = async () => {
    await AudioModule.setAudioModeAsync({
      allowsRecording: true,
      playsInSilentMode: true,
      interruptionMode: "mixWithOthers",
      interruptionModeAndroid: "doNotMix",
      shouldPlayInBackground: false,
      shouldRouteThroughEarpiece: false,
    });
    await AudioModule.setIsAudioActiveAsync(true);
  };

  const persistRecording = async (uri: string) => {
    // Parse the uri to construct File instances reliably
    const parsed = Paths.parse(uri);
    const sourceFile = new File(parsed.dir, parsed.base);
    if (!sourceFile.exists) {
      throw new Error("El archivo de audio no existe");
    }

    const destinationDir = Paths.document ?? Paths.cache;
    const destinationFile = new File(destinationDir, `audio-${Date.now()}.m4a`);
    // Copy the file to a persistent location (await to ensure operation completes)
    await sourceFile.copy(destinationFile);
    return destinationFile.uri;
  };

  const deleteFileIfExists = (uri: string) => {
    try {
      const parsed = Paths.parse(uri);
      const file = new File(parsed.dir, parsed.base);
      if (file.exists) {
        file.delete();
      }
    } catch {
      // Ignore cleanup issues
    }
  };

  const startRecording = async () => {
    try {
      const status = await AudioModule.requestRecordingPermissionsAsync();
      if (!status.granted) {
        Alert.alert(
          "Permiso denegado",
          "Se requiere acceso al micrófono para grabar audio",
        );
        return;
      }

      await configureAudioSession();

      // Prepare the recorder (useAudioRecorder provides the recorder instance)
      if (typeof recorder.prepareToRecordAsync === "function") {
        await (recorder as any).prepareToRecordAsync();
      }

      recorder.record();
      setIsRecording(true);
      setRecordingDuration(0);
    } catch (error: any) {
      Alert.alert("Error", `No se pudo iniciar la grabación: ${error.message}`);
    }
  };

  const stopRecording = async () => {
    try {
      setIsRecording(false);

      if (recorder) {
        await (recorder as any).stop();
        const uri = recorder.uri;

        if (uri) {
          const persistedUri = await persistRecording(uri);
          try {
            await processAudio(persistedUri);
          } finally {
            deleteFileIfExists(persistedUri);
          }
        }
      }
    } catch (error: any) {
      Alert.alert("Error", `Error al detener grabación: ${error.message}`);
    } finally {
      try {
        await AudioModule.setIsAudioActiveAsync(false);
      } catch {
        // ignore cleanup errors
      }
    }
  };

  const processAudio = async (uri: string) => {
    if (!user) {
      Alert.alert("Error", "Usuario no autenticado");
      return;
    }

    setProcessing(true);
    setProcessingStep("Preparando audio...");

    try {
      const timestamp = Date.now();
      const fileName = `audio_${timestamp}.m4a`;

      setProcessingStep("Subiendo audio...");

      const response = await processFile(
        {
          uri,
          name: fileName,
          type: "audio/m4a",
        },
        user.id,
        null,
        "general",
      );

      setProcessingStep("Transcribiendo...");

      if (response.data) {
        setResult(response.data);

        const tx = response.data.transaction;
        const parsed = response.data.parsed_data;
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
              response.data.category?.id ||
              categories[0]?.id ||
              1,
            source_id:
              tx.source_id || response.data.source?.id || sources[0]?.id || 1,
            state: tx.state || "pending",
          });
        }
      }
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Error al procesar";
      Alert.alert("Error", errorMessage);
    } finally {
      setProcessing(false);
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

      Alert.alert("Éxito", "Transacción creada desde audio", [
        { text: "OK", onPress: () => router.push("/transactions") },
      ]);
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail || error.message || "Error al guardar";
      Alert.alert("Error", errorMessage);
    } finally {
      setSaving(false);
    }
  };

  const resetScreen = () => {
    setResult(null);
    setEditableTransaction(null);
    setRecordingDuration(0);
  };

  return (
    <ThemedView
      style={[styles.container, { backgroundColor: theme.background }]}
    >
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <ThemedText
            type="title"
            style={[styles.title, { color: theme.text }]}
          >
            Transacción por Voz
          </ThemedText>
          <ThemedText style={[styles.subtitle, { color: theme.icon }]}>
            Dicta tu transacción y se creará automáticamente
          </ThemedText>
        </View>

        {!result ? (
          <>
            {/* Recording UI */}
            <View
              style={[
                styles.recordingCard,
                { backgroundColor: isDark ? "#222" : theme.cardBackground },
              ]}
            >
              {/* Microphone Icon */}
              <View
                style={[
                  styles.micContainer,
                  {
                    backgroundColor: isRecording
                      ? "#ff6b6b22"
                      : theme.tint + "22",
                  },
                ]}
              >
                <IconSymbol
                  name={isRecording ? ("waveform" as any) : ("mic.fill" as any)}
                  size={48}
                  color={isRecording ? "#ff6b6b" : theme.tint}
                />
              </View>

              {/* Duration */}
              {(isRecording || recordingDuration > 0) && (
                <ThemedText
                  style={[
                    styles.duration,
                    { color: isRecording ? "#ff6b6b" : theme.text },
                  ]}
                >
                  {formatDuration(recordingDuration)}
                </ThemedText>
              )}

              {/* Instructions */}
              <ThemedText style={[styles.instructions, { color: theme.icon }]}>
                {isRecording
                  ? 'Grabando... Di algo como:\n"Gasté 50 dólares en comida"'
                  : "Presiona el botón para grabar"}
              </ThemedText>

              {/* Processing indicator */}
              {processing && (
                <View style={styles.processingContainer}>
                  <ActivityIndicator color={theme.tint} size="small" />
                  <ThemedText
                    style={[styles.processingText, { color: theme.icon }]}
                  >
                    {processingStep}
                  </ThemedText>
                </View>
              )}

              {/* Record Button */}
              <Pressable
                onPress={isRecording ? stopRecording : startRecording}
                disabled={processing}
                style={[
                  styles.recordButton,
                  {
                    backgroundColor: isRecording ? "#ff6b6b" : theme.tint,
                    opacity: processing ? 0.5 : 1,
                  },
                ]}
              >
                <IconSymbol
                  name={
                    isRecording ? ("stop.fill" as any) : ("mic.fill" as any)
                  }
                  size={32}
                  color="#fff"
                />
              </Pressable>

              <ThemedText style={[styles.buttonLabel, { color: theme.icon }]}>
                {isRecording ? "Detener" : "Grabar"}
              </ThemedText>
            </View>

            {/* Tips */}
            <View style={styles.tipsContainer}>
              <ThemedText style={[styles.tipsTitle, { color: theme.text }]}>
                💡 Ejemplos de lo que puedes decir:
              </ThemedText>
              <ThemedText style={[styles.tipText, { color: theme.icon }]}>
                • Pagué 120 pesos de luz
              </ThemedText>
              <ThemedText style={[styles.tipText, { color: theme.icon }]}>
                • Recibí 500 dólares de mi trabajo
              </ThemedText>
              <ThemedText style={[styles.tipText, { color: theme.icon }]}>
                • Gasté 30 en uber
              </ThemedText>
            </View>

            {/* Back button */}
            <Pressable
              onPress={() => router.back()}
              style={[styles.backButton, { borderColor: theme.icon }]}
            >
              <ThemedText
                style={[styles.backButtonText, { color: theme.icon }]}
              >
                Volver
              </ThemedText>
            </Pressable>
          </>
        ) : (
          <>
            {/* Result / Edit Form */}
            <View
              style={[
                styles.resultCard,
                { backgroundColor: isDark ? "#222" : theme.cardBackground },
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
                  Audio procesado
                </ThemedText>
              </View>

              {/* Transcription preview */}
              {result.extraction?.raw_text && (
                <View
                  style={[
                    styles.transcriptionBox,
                    { backgroundColor: isDark ? "#111" : "#f5f5f5" },
                  ]}
                >
                  <ThemedText
                    style={[styles.transcriptionLabel, { color: theme.icon }]}
                  >
                    Texto transcrito:
                  </ThemedText>
                  <ThemedText
                    style={[styles.transcriptionText, { color: theme.text }]}
                  >
                    {result.extraction.raw_text}
                  </ThemedText>
                </View>
              )}

              {editableTransaction && (
                <>
                  <View style={styles.divider} />

                  <ThemedText
                    style={[styles.sectionLabel, { color: theme.text }]}
                  >
                    Revisar transacción:
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
                      numberOfLines={2}
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

                  {/* Type */}
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
                              {src.name}
                            </ThemedText>
                          </Pressable>
                        ))}
                      </View>
                    </ScrollView>
                  </View>
                </>
              )}

              {/* Actions */}
              <View style={styles.actions}>
                <Pressable
                  onPress={updateTransaction}
                  disabled={saving}
                  style={[
                    styles.confirmButton,
                    { backgroundColor: "#22c55e", opacity: saving ? 0.6 : 1 },
                  ]}
                >
                  {saving ? (
                    <ActivityIndicator color="#fff" size="small" />
                  ) : (
                    <ThemedText style={styles.confirmButtonText}>
                      ✓ Confirmar
                    </ThemedText>
                  )}
                </Pressable>
              </View>

              <View style={styles.secondaryActions}>
                <Pressable
                  onPress={resetScreen}
                  style={[styles.secondaryButton, { borderColor: theme.icon }]}
                >
                  <ThemedText
                    style={[styles.secondaryButtonText, { color: theme.icon }]}
                  >
                    Grabar otro
                  </ThemedText>
                </Pressable>
                <Pressable
                  onPress={() => router.push("/transactions")}
                  style={[styles.secondaryButton, { borderColor: theme.tint }]}
                >
                  <ThemedText
                    style={[styles.secondaryButtonText, { color: theme.tint }]}
                  >
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
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
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
  recordingCard: {
    margin: 20,
    borderRadius: 20,
    padding: 30,
    alignItems: "center",
  },
  micContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
  },
  duration: {
    fontSize: 32,
    fontWeight: "700",
    marginBottom: 16,
  },
  instructions: {
    fontSize: 14,
    textAlign: "center",
    marginBottom: 24,
    lineHeight: 22,
  },
  processingContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 20,
  },
  processingText: {
    marginLeft: 10,
    fontSize: 14,
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  buttonLabel: {
    fontSize: 14,
    fontWeight: "600",
  },
  tipsContainer: {
    paddingHorizontal: 20,
    marginTop: 10,
  },
  tipsTitle: {
    fontSize: 15,
    fontWeight: "700",
    marginBottom: 10,
  },
  tipText: {
    fontSize: 13,
    marginBottom: 6,
  },
  backButton: {
    marginHorizontal: 20,
    marginTop: 24,
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
    borderWidth: 1,
  },
  backButtonText: {
    fontWeight: "700",
  },
  resultCard: {
    margin: 20,
    borderRadius: 20,
    padding: 20,
  },
  resultHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginLeft: 10,
  },
  transcriptionBox: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  transcriptionLabel: {
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 8,
  },
  transcriptionText: {
    fontSize: 15,
    fontStyle: "italic",
  },
  divider: {
    height: 1,
    backgroundColor: "#e0e0e0",
    marginVertical: 16,
  },
  sectionLabel: {
    fontSize: 16,
    fontWeight: "700",
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
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
  },
  textArea: {
    minHeight: 60,
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
  actions: {
    marginTop: 20,
  },
  confirmButton: {
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: "center",
  },
  confirmButtonText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 16,
  },
  secondaryActions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 12,
  },
  secondaryButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: "center",
    borderWidth: 1,
  },
  secondaryButtonText: {
    fontWeight: "700",
    fontSize: 14,
  },
});
