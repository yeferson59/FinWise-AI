import React, { useState } from "react";
import { View, Text, TextInput, Button, Alert, StyleSheet } from "react-native";
import { login } from "shared/api";

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");

  const handleLogin = async () => {
    try {
      const res = await login(email, pass);

      console.log("LOGIN RESPONSE:", res.data);

      // 🔥 Validación REAL del backend
      if (!res.data.success) {
        Alert.alert("Error", "Credenciales incorrectas");
        return;
      }

      Alert.alert("Éxito", "Inicio de sesión correcto");
      navigation.navigate("HomeMain"); // ahora sí
    } catch (e) {
      console.log("LOGIN ERROR:", e);
      Alert.alert("Error", "No se pudo conectar al servidor");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Login</Text>

      <TextInput
        placeholder="Correo"
        value={email}
        onChangeText={setEmail}
        style={styles.input}
      />

      <TextInput
        placeholder="Clave"
        value={pass}
        onChangeText={setPass}
        secureTextEntry
        style={styles.input}
      />

      <Button title="Entrar" onPress={handleLogin} />

      <Text
        style={styles.link}
        onPress={() => navigation.navigate("Register")}
      >
        ¿No tienes cuenta? Regístrate
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 20 },
  title: { fontSize: 24, marginBottom: 20, textAlign: "center" },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 10,
    marginVertical: 5,
    borderRadius: 5,
  },
  link: {
    marginTop: 20,
    color: "blue",
    textAlign: "center",
  },
});







/*import { useState } from "react";
import { View, Text, TextInput, Button, StyleSheet, Alert } from "react-native";
import { login } from "shared/api";
import { useRouter } from "expo-router";

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");

  const handleLogin = async () => {
    try {
      const res = await login(email, pass);
      console.log("LOGIN OK:", res.data);

      Alert.alert("Éxito", "Inicio de sesión correcto");

      router.push("/home"); // → Navegar al Home
    } catch (err) {
      console.log("ERROR LOGIN:", err?.response?.data);
      Alert.alert("Error", "Credenciales incorrectas");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Login</Text>

      <TextInput
        style={styles.input}
        placeholder="Correo"
        value={email}
        onChangeText={setEmail}
      />

      <TextInput
        style={styles.input}
        placeholder="Contraseña"
        secureTextEntry
        value={pass}
        onChangeText={setPass}
      />

      <Button title="Entrar" onPress={handleLogin} />

      <Text style={styles.link} onPress={() => router.push("/register")}>
        ¿No tienes cuenta? Regístrate
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 20 },
  title: { fontSize: 28, marginBottom: 20, textAlign: "center" },
  input: {
    borderWidth: 1,
    padding: 10,
    marginBottom: 10,
    borderRadius: 6,
  },
  link: { marginTop: 15, color: "blue", textAlign: "center" },
});
*/