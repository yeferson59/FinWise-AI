// navigation/AppNavigator.js
import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";

import LoginScreen from "../screens/LoginScreen";
import RegisterScreen from "../screens/RegisterScreen";
import HomeScreen from "../screens/HomeScreen";
import DrawerNavigation from "./DrawerNavigation";

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>

        {/* Login */}
        <Stack.Screen name="Login" component={LoginScreen} />

        {/* Registro */}
        <Stack.Screen name="Register" component={RegisterScreen} />

        {/* Home + Drawer */}
        <Stack.Screen name="HomeMain" component={DrawerNavigation} />

      </Stack.Navigator>
    </NavigationContainer>
  );
}