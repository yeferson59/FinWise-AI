import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  Button,
  StyleSheet,
  Alert,
  ScrollView,
} from "react-native";

import * as DocumentPicker from "expo-document-picker";
import { processText, processFile } from "shared/api";

export default function TransactionScreen() {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState([]);

  // mock user
  const user_id = 1;
  const source_id = 1;

  const addMessage = (sender, msg) => {
    setMessages((prev) => [...prev, { sender, text: msg }]);
  };

  // --- SEND TEXT TO NLP ---
  const handleSendText = async () => {
    if (!text.trim()) return;

    addMessage("user", text);
    setText("");

    try {
      const res = await processText(text, user_id, source_id);
      console.log("NLP RESULT:", res.data);

      const tx = res.data.transaction;
      addMessage(
        "system",
        `✔ Guardado: ${tx.description} — $${tx.amount} (${tx.category_id})`
      );

    } catch (err) {
      console.log("ERR NLP:", err.response?.data);
      addMessage("system", "❌ Error procesando texto");
    }
  };

  // --- SEND FILE TO NLP+OCR ---
  const handleSendFile = async () => {
  try {
    const result = await DocumentPicker.getDocumentAsync({
      copyToCacheDirectory: true,
    });

    if (!result.assets?.length) return;

    const file = result.assets[0];

    addMessage("user", `📎 Enviando archivo: ${file.name}`);

    const fileToSend = {
      uri: file.uri,
      name: file.name ?? `upload-${Date.now()}.jpg`,
      type: file.mimeType ?? file.type ?? "image/jpeg",
    };

    const res = await processFile(fileToSend, 1, 1);

    console.log("OCR NLP RESULT:", res.data);

    const tx = res.data.transaction;

    addMessage(
      "system",
      `📄 Guardado: ${tx.description} — $${tx.amount} (${tx.category_id})`
    );

  } catch (err) {
    console.log("FULL FILE ERROR:", err);
    console.log("AXIOS ERR RESPONSE:", err?.response?.data);
    console.log("AXIOS ERR REQUEST:", err?.request);
    
    addMessage("system", "❌ Error procesando archivo");
  }
};


  return (
    <View style={styles.container}>
      <ScrollView style={styles.chat}>
        {messages.map((m, i) => (
          <Text
            key={i}
            style={{
              alignSelf: m.sender === "user" ? "flex-end" : "flex-start",
              backgroundColor: m.sender === "user" ? "#d1e7ff" : "#eee",
              padding: 10,
              borderRadius: 8,
              marginVertical: 4,
              maxWidth: "80%",
            }}
          >
            {m.text}
          </Text>
        ))}
      </ScrollView>

      <TextInput
        style={styles.input}
        placeholder="Ej: Pagué 20.000 en comida"
        value={text}
        onChangeText={setText}
      />

      <Button title="Enviar texto" onPress={handleSendText} />
      <View style={{ height: 10 }} />
      <Button title="Subir imagen / PDF" onPress={handleSendFile} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 10, backgroundColor: "#fff" },
  chat: { flex: 1, marginBottom: 10 },
  input: {
    borderWidth: 1,
    borderColor: "#aaa",
    padding: 10,
    marginBottom: 10,
    borderRadius: 6,
  },
});
