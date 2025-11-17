import { useState } from "react";
import { View, Text, TextInput, Button, Alert, StyleSheet } from "react-native";
import { Checkbox } from "expo-checkbox";
import { register } from "shared/api";

export default function RegisterScreen({ navigation }: { navigation: any }) {
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [confirm_pass, setConfirm] = useState("");
  const [terms, setTerms] = useState(false);
  const handleRegister = async () => {
    try {
      await register(first, last, email, pass, confirm_pass, terms);
      Alert.alert("Éxito", "Usuario registrado correctamente");

      navigation.navigate("Login");
    } catch (error: any) {
      console.log("ERROR REGISTER:", error);
      console.log("DATA:", error?.response?.data);

      if (error?.response?.data) {
        Alert.alert("Error", JSON.stringify(error.response.data, null, 2));
      } else {
        Alert.alert("Error", error.message || "Error desconocido");
      }
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Registro</Text>

      <TextInput
        style={styles.input}
        placeholder="Nombre"
        value={first}
        onChangeText={setFirst}
      />
      <TextInput
        style={styles.input}
        placeholder="Apellido"
        value={last}
        onChangeText={setLast}
      />
      <TextInput
        style={styles.input}
        placeholder="Correo"
        value={email}
        onChangeText={setEmail}
      />
      <TextInput
        style={styles.input}
        placeholder="Clave"
        value={pass}
        onChangeText={setPass}
        secureTextEntry
      />
      <TextInput
        style={styles.input}
        placeholder="Confirmar Clave"
        value={confirm_pass}
        onChangeText={setConfirm}
        secureTextEntry
      />
      <Checkbox
        value={terms}
        onValueChange={setTerms}
        color={terms ? "#4630EB" : undefined}
      />
      <Text>Acepto términos y condiciones</Text>

      <Button title="Crear cuenta" onPress={handleRegister} />
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
});
