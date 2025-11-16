import AppNavigator from "./navigation/AppNavigator";

export default function App() {
  return <AppNavigator />;
}




/*import React, { useState } from "react";
import { 
  View, 
  Text, 
  TextInput, 
  Button, 
  StyleSheet,
  Alert 
} from "react-native";
import { login } from "shared/api";  // <--- tu API compartida

export default function App() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert("Error", "Completa todos los campos.");
      return;
    }

    try {
      const response = await login(email, password);
      console.log("LOGIN OK:", response.data);
      Alert.alert("Éxito", "Inicio de sesión correcto ✅");

    } catch (error) {
      console.log("ERROR LOGIN:", error?.response?.data);
      Alert.alert(
        "Error",
        error?.response?.data?.detail ?? "No se pudo iniciar sesión."
      );
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
        autoCapitalize="none"
      />

      <TextInput
        style={styles.input}
        placeholder="Contraseña"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />

      <Button title="Ingresar" onPress={handleLogin} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: 25
  },
  title: {
    fontSize: 26,
    textAlign: "center",
    marginBottom: 20,
    fontWeight: "bold"
  },
  input: {
    borderWidth: 1,
    borderColor: "#999",
    padding: 12,
    marginBottom: 12,
    borderRadius: 8
  }
});*/
