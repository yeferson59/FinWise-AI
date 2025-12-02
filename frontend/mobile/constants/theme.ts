/**
 * Below are the colors that are used in the app. The colors are defined in the light and dark mode.
 * There are many other ways to style your app. For example, [Nativewind](https://www.nativewind.dev/), [Tamagui](https://tamagui.dev/), [unistyles](https://reactnativeunistyles.vercel.app), etc.
 */

import { Platform } from "react-native";

const tintColorLight = "#007bff"; // Azul principal
const tintColorDark = "#4da6ff"; // Azul claro para modo oscuro

const secondaryGreen = "#28a745"; // Verde
const accentWhite = "#ffffff"; // Blanco
const backgroundLight = "#f8f9fa"; // Fondo gris claro
const textDark = "#212529"; // Texto oscuro

export const Colors = {
  light: {
    text: textDark,
    background: accentWhite,
    tint: tintColorLight,
    icon: "#6c757d",
    tabIconDefault: "#6c757d",
    tabIconSelected: tintColorLight,
    primary: tintColorLight,
    secondary: secondaryGreen,
    accent: accentWhite,
    cardBackground: accentWhite,
    inputBackground: backgroundLight,
    buttonPrimary: tintColorLight,
    buttonSecondary: secondaryGreen,
    buttonText: "#ffffff",
    shadow: "rgba(0, 123, 255, 0.1)",
  },
  dark: {
    text: "#ECEDEE",
    background: "#1a1a1a",
    tint: tintColorDark,
    icon: "#9BA1A6",
    tabIconDefault: "#9BA1A6",
    tabIconSelected: tintColorDark,
    primary: tintColorDark,
    secondary: secondaryGreen,
    accent: accentWhite,
    cardBackground: "#2a2a2a",
    inputBackground: "#333",
    buttonPrimary: tintColorDark,
    buttonSecondary: secondaryGreen,
    buttonText: "#1a1a1a",
    shadow: "rgba(0, 123, 255, 0.2)",
  },
};

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: "system-ui",
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: "ui-serif",
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: "ui-rounded",
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: "ui-monospace",
  },
  default: {
    sans: "normal",
    serif: "serif",
    rounded: "normal",
    mono: "monospace",
  },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    serif: "Georgia, 'Times New Roman', serif",
    rounded:
      "'SF Pro Rounded', 'Hiragino Maru Gothic ProN', Meiryo, 'MS PGothic', sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  },
});

/**
 * Cross-platform shadow utility
 * Takes an rgba color string and applies it appropriately
 * For native: parses rgba to rgb and opacity
 * For web: uses rgba directly
 */
export const createShadow = (
  offsetX: number,
  offsetY: number,
  radius: number,
  rgbaColor: string = "rgba(0,0,0,0.1)",
  elevation?: number,
) => {
  if (Platform.OS === "web") {
    return {
      boxShadow: `${offsetX}px ${offsetY}px ${radius}px ${rgbaColor}`,
    };
  }
  // Parse rgba color for native
  const match = rgbaColor.match(
    /rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/,
  );
  if (!match) {
    // Fallback
    return {
      shadowOffset: { width: offsetX, height: offsetY },
      shadowOpacity: 0.1,
      shadowRadius: radius,
      elevation: elevation ?? Math.max(offsetY, radius),
    };
  }
  const r = match[1],
    g = match[2],
    b = match[3],
    a = match[4] ? parseFloat(match[4]) : 1;
  return {
    shadowColor: `rgb(${r},${g},${b})`,
    shadowOffset: { width: offsetX, height: offsetY },
    shadowOpacity: a,
    shadowRadius: radius,
    elevation: elevation ?? Math.max(offsetY, radius),
  };
};

/**
 * Predefined shadow styles
 */
export const Shadows = {
  small: createShadow(0, 2, 4, "rgba(0,0,0,0.1)"),
  medium: createShadow(0, 4, 8, "rgba(0,0,0,0.12)"),
  large: createShadow(0, 6, 12, "rgba(0,0,0,0.15)"),
  extraLarge: createShadow(0, 8, 16, "rgba(0,0,0,0.2)"),
};
