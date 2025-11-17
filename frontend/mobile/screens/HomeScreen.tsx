import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

export default function HomeScreen({ navigation }: { navigation: any }) {
  return (
    <View style={styles.container}>
      {/* ENCABEZADO */}
      <View style={styles.header}>
        <Text style={styles.title}>Mi Panel Financiero</Text>

        {/* BOTÓN DEL MENÚ */}
        <TouchableOpacity onPress={() => navigation.openDrawer()}>
          <Ionicons name="menu" size={32} color="#333" />
        </TouchableOpacity>
      </View>

      {/* TARJETAS */}
      <View style={styles.card}>
        <Text style={styles.label}>💰 Balance actual</Text>
        <Text style={styles.value}>$ 1,250.00</Text>
      </View>

      <View style={styles.row}>
        <View style={styles.smallCard}>
          <Text style={styles.label}>📈 Ingresos</Text>
          <Text style={styles.value}>$ 4,000.00</Text>
        </View>

        <View style={styles.smallCard}>
          <Text style={styles.label}>📉 Gastos</Text>
          <Text style={styles.value}>$ 2,750.00</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: "#fff" },

  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },

  title: { fontSize: 24, fontWeight: "bold" },

  card: {
    padding: 20,
    backgroundColor: "#e3f2fd",
    borderRadius: 10,
    marginBottom: 20,
  },

  row: {
    flexDirection: "row",
    justifyContent: "space-between",
  },

  smallCard: {
    width: "48%",
    padding: 20,
    backgroundColor: "#f1f8e9",
    borderRadius: 10,
  },

  label: { fontSize: 16 },
  value: { fontSize: 20, fontWeight: "bold", marginTop: 10 },
});
