import { useState, useRef, useEffect, useCallback } from "react";
import {
  View,
  StyleSheet,
  Pressable,
  TextInput,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { ThemedText } from "@/components/themed-text";
import { Colors, createShadow } from "@/constants/theme";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { useAuth } from "@/contexts/AuthContext";
import { sendAgentMessage, type ChatMessage } from "shared";

/**
 * AI Assistant chat screen
 * - Real-time chat with FinWise AI agent
 * - Supports financial queries and analysis
 * - Agent is scoped to only access authenticated user's data
 */

export default function AssistantScreen() {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? "light"];
  const isDark = (colorScheme ?? "light") === "dark";
  const { user } = useAuth();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const generateId = () => `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

  const scrollToBottom = useCallback(() => {
    if (flatListRef.current && messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = async () => {
    const trimmedText = inputText.trim();
    if (!trimmedText || isLoading || !user?.id) return;

    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content: trimmedText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText("");
    setIsLoading(true);

    try {
      // Pass user.id to scope the agent to only access this user's data
      const response = await sendAgentMessage(trimmedText, user.id);

      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: "Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === "user";

    return (
      <View
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.assistantMessageContainer,
        ]}
      >
        {!isUser && (
          <View
            style={[
              styles.avatarContainer,
              { backgroundColor: isDark ? "#062f24" : "#eef6f5" },
            ]}
          >
            <IconSymbol name={"sparkles" as any} size={16} color={theme.tint} />
          </View>
        )}
        <View
          style={[
            styles.messageBubble,
            isUser
              ? [styles.userBubble, { backgroundColor: theme.tint }]
              : [
                  styles.assistantBubble,
                  {
                    backgroundColor: theme.cardBackground,
                    ...createShadow(0, 2, 4, theme.shadow, 2),
                  },
                ],
          ]}
        >
          <ThemedText
            style={[
              styles.messageText,
              { color: isUser ? "#fff" : theme.text },
            ]}
          >
            {item.content}
          </ThemedText>
          <ThemedText
            style={[
              styles.messageTime,
              { color: isUser ? "rgba(255,255,255,0.7)" : theme.icon },
            ]}
          >
            {item.timestamp.toLocaleTimeString("es-ES", {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </ThemedText>
        </View>
      </View>
    );
  };

  const renderEmptyState = () => (
    <View style={styles.emptyState}>
      <View
        style={[
          styles.emptyStateIcon,
          { backgroundColor: isDark ? "rgba(37, 209, 178, 0.16)" : "rgba(37, 209, 178, 0.08)" },
        ]}
      >
        <IconSymbol name={"sparkles" as any} size={32} color={theme.tint} />
      </View>
      <ThemedText style={[styles.emptyStateTitle, { color: theme.text }]}>
        FinWise AI
      </ThemedText>
      <ThemedText style={[styles.emptyStateSubtitle, { color: theme.icon }]}>
        Tu asistente financiero inteligente
      </ThemedText>
      <View style={styles.suggestionsContainer}>
        {[
          "¿Cuánto gasté este mes?",
          "¿Cuáles son mis categorías?",
          "Resume mis transacciones",
        ].map((suggestion, index) => (
          <Pressable
            key={index}
            style={[
              styles.suggestionChip,
              {
                backgroundColor: theme.cardBackground,
                borderColor: isDark ? "#333" : "#e0e0e0",
              },
            ]}
            onPress={() => setInputText(suggestion)}
          >
            <ThemedText style={[styles.suggestionText, { color: theme.text }]}>
              {suggestion}
            </ThemedText>
          </Pressable>
        ))}
      </View>
    </View>
  );

  const renderTypingIndicator = () => (
    <View style={[styles.messageContainer, styles.assistantMessageContainer]}>
      <View
        style={[
          styles.avatarContainer,
          { backgroundColor: isDark ? "#062f24" : "#eef6f5" },
        ]}
      >
        <IconSymbol name={"sparkles" as any} size={16} color={theme.tint} />
      </View>
      <View
        style={[
          styles.messageBubble,
          styles.assistantBubble,
          {
            backgroundColor: theme.cardBackground,
            ...createShadow(0, 2, 4, theme.shadow, 2),
          },
        ]}
      >
        <View style={styles.typingIndicator}>
          <ActivityIndicator size="small" color={theme.tint} />
          <ThemedText style={[styles.typingText, { color: theme.icon }]}>
            Pensando...
          </ThemedText>
        </View>
      </View>
    </View>
  );

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: theme.inputBackground }]}
      edges={["top"]}
    >
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View
            style={[
              styles.headerIcon,
              { backgroundColor: isDark ? "#062f24" : "#eef6f5" },
            ]}
          >
            <IconSymbol name={"sparkles" as any} size={20} color={theme.tint} />
          </View>
          <View>
            <ThemedText style={[styles.headerTitle, { color: theme.text }]}>
              Asistente IA
            </ThemedText>
            <ThemedText style={[styles.headerSubtitle, { color: theme.icon }]}>
              {isLoading ? "Escribiendo..." : "En línea"}
            </ThemedText>
          </View>
        </View>
      </View>

      <KeyboardAvoidingView
        style={styles.chatContainer}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerStyle={[
            styles.messagesList,
            messages.length === 0 && styles.emptyMessagesList,
          ]}
          ListEmptyComponent={renderEmptyState}
          ListFooterComponent={isLoading ? renderTypingIndicator : null}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={scrollToBottom}
        />

        <View
          style={[
            styles.inputContainer,
            {
              backgroundColor: theme.cardBackground,
              borderTopColor: isDark ? "#333" : "#e0e0e0",
            },
          ]}
        >
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: theme.inputBackground,
                color: theme.text,
                borderColor: isDark ? "#444" : "#ddd",
              },
            ]}
            placeholder="Escribe tu mensaje..."
            placeholderTextColor={theme.icon}
            value={inputText}
            onChangeText={setInputText}
            multiline
            maxLength={1000}
            editable={!isLoading}
            onSubmitEditing={sendMessage}
            returnKeyType="send"
          />
          <Pressable
            onPress={sendMessage}
            disabled={!inputText.trim() || isLoading}
            style={({ pressed }) => [
              styles.sendButton,
              {
                backgroundColor:
                  !inputText.trim() || isLoading
                    ? isDark
                      ? "#333"
                      : "#ccc"
                    : pressed
                      ? isDark
                        ? "#0f5132"
                        : "#1ba97e"
                      : theme.tint,
              },
            ]}
          >
            <IconSymbol
              name={"arrow.up" as any}
              size={18}
              color={!inputText.trim() || isLoading ? theme.icon : "#fff"}
            />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
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
    borderBottomWidth: 1,
    borderBottomColor: "rgba(128,128,128,0.2)",
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  headerIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: "700",
  },
  headerSubtitle: {
    fontSize: 12,
    marginTop: 2,
  },
  chatContainer: {
    flex: 1,
  },
  messagesList: {
    padding: 16,
    paddingBottom: 8,
  },
  emptyMessagesList: {
    flex: 1,
    justifyContent: "center",
  },
  messageContainer: {
    flexDirection: "row",
    marginBottom: 12,
    maxWidth: "85%",
  },
  userMessageContainer: {
    alignSelf: "flex-end",
    flexDirection: "row-reverse",
  },
  assistantMessageContainer: {
    alignSelf: "flex-start",
  },
  avatarContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 8,
    marginTop: 4,
  },
  messageBubble: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 18,
    maxWidth: "100%",
  },
  userBubble: {
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 21,
  },
  messageTime: {
    fontSize: 10,
    marginTop: 4,
    alignSelf: "flex-end",
  },
  typingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 4,
  },
  typingText: {
    fontSize: 13,
    marginLeft: 8,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 1,
  },
  textInput: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    fontSize: 15,
    marginRight: 10,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyState: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
  },
  emptyStateIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  emptyStateTitle: {
    fontSize: 22,
    fontWeight: "800",
    marginBottom: 6,
  },
  emptyStateSubtitle: {
    fontSize: 14,
    textAlign: "center",
    marginBottom: 24,
  },
  suggestionsContainer: {
    width: "100%",
  },
  suggestionChip: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    marginBottom: 8,
  },
  suggestionText: {
    fontSize: 14,
    textAlign: "center",
  },
});
