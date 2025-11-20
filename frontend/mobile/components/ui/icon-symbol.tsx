// Fallback for using MaterialIcons on Android and web.

import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { ComponentProps } from "react";
import { OpaqueColorValue, type StyleProp, type TextStyle } from "react-native";

type IconMapping = Record<string, ComponentProps<typeof MaterialIcons>["name"]>;

/**
 * Add your SF Symbols to Material Icons mappings here.
 * - see Material Icons in the [Icons Directory](https://icons.expo.fyi).
 * - see SF Symbols in the [SF Symbols](https://developer.apple.com/sf-symbols/) app.
 *
 * This mapping contains common SF symbol names mapped to Material Icon names.
 * You can extend it as you adopt additional icons across the app.
 */
const MAPPING: IconMapping = {
  "house.fill": "home",
  "paperplane.fill": "send",
  "chevron.left.forwardslash.chevron.right": "code",
  "chevron.right": "chevron-right",

  // Helpful mappings for icons used in the app (fallbacks)
  plus: "add",
  "swap.horizontal": "swap-horiz",
  "trending.up": "trending-up",
  wallet: "account-balance-wallet",
  menu: "menu",
  pizza: "local-pizza",
  car: "directions-car",
  home: "home",
};

/**
 * An icon component that uses native SF Symbols on iOS, and Material Icons on Android and web.
 * On non-iOS platforms it looks up a Material Icon name from the mapping above;
 * if no mapping exists, it falls back to a safe default.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: string;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
  weight?: any;
}) {
  const mapped = MAPPING[name] ?? "help-outline";
  return (
    <MaterialIcons
      color={color}
      size={size}
      name={mapped as any}
      style={style}
    />
  );
}
