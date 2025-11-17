import React from "react";
import { createDrawerNavigator } from "@react-navigation/drawer";
import HomeScreen from "../screens/HomeScreen";
import RegistrarTransaccion from "../screens/TransactionScreen";
import SaludFinanciera from "../screens/FinanceScreen";
import AsistenteVirtual from "../screens/AssistantScreen";
import Notificaciones from "../screens/NotificationScreen";

const Drawer = createDrawerNavigator();

export default function DrawerNavigation() {
  return (
    <Drawer.Navigator screenOptions={{ headerShown: false }}>
      
      {/* Home dentro del drawer también, pero NO se usa como pantalla inicial */}
      <Drawer.Screen name="Home" component={HomeScreen} />

      <Drawer.Screen name="Registrar Transacción" component={RegistrarTransaccion} />
      <Drawer.Screen name="Mi Salud Financiera" component={SaludFinanciera} />
      <Drawer.Screen name="Asistente Virtual" component={AsistenteVirtual} />
      <Drawer.Screen name="Notificaciones" component={Notificaciones} />

    </Drawer.Navigator>
  );
}
