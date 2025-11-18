# FinWise-AI Mobile App - Overview & Aesthetic Guide

## 🎨 App Overview

FinWise-AI is a modern financial management mobile application built with Expo and React Native. The app provides comprehensive financial tracking, AI-powered insights, and intuitive expense management features.

## 📱 Core Features

### Authentication

- **Login Screen** (`app/login.tsx`) - Email/password authentication with validation
- **Register Screen** (`app/register.tsx`) - User registration with terms acceptance
- Clean, professional design with form validation feedback

### Dashboard

- **Home Screen** (`app/home.tsx`) - Main dashboard with:
  - Balance overview with percentage change indicator
  - Income/Expense summary
  - Quick action buttons (Add, Transfer, Statistics, Budget)
  - Expense categories breakdown with progress bars
  - Expense filtering by time period (Day/Week/Month/Year)

### Navigation

- **Menu Screen** (`app/menu.tsx`) - Hamburger menu modal with:
  - 10 main navigation options
  - Quick action buttons
  - Logout functionality
  - Smooth animations
  - Theme-aware styling

### Financial Management

- **Transactions** (`app/transactions.tsx`) - View all financial transactions
- **Categories** (`app/categories.tsx`) - Manage expense categories
- **Budget** (`app/budget.tsx`) - Create and track budgets
- **Reports** (`app/reports.tsx`) - Generate financial reports

### Additional Features

- **Profile** (`app/profile.tsx`) - User account information and settings
- **Settings** (`app/settings.tsx`) - App preferences and configuration
- **AI Assistant** (`app/assistant.tsx`) - AI-powered financial guidance
- **OCR** (`app/ocr.tsx`) - Receipt and invoice scanning
- **Integrations** (`app/integrations.tsx`) - Bank and multi-currency support
- **Notifications** (`app/notifications.tsx`) - Alerts and reminders

## 🎨 Aesthetic & Design System

### Color Scheme

The app uses a sophisticated color system with light and dark mode support:

**Light Mode:**

- Background: `#FFFFFF`
- Cards: `#F8FAFB`
- Text: `#1A1A1A`
- Secondary Text: `#666666`
- Accent/Tint: `#0B7285` (Teal)

**Dark Mode:**

- Background: `#0A0A0A`
- Cards: `#1A1A1A`
- Text: `#FFFFFF`
- Secondary Text: `#AAAAAA`
- Accent/Tint: `#25D1B2` (Cyan)

### Typography

- **Headlines**: 26px, Weight 800 (Extra Bold)
- **Titles**: 18px, Weight 800
- **Labels**: 16px, Weight 700 (Bold)
- **Body Text**: 15px, Weight 500
- **Small Text**: 13px, Weight 400 (Regular)

### Component Styling

#### Cards & Containers

- **Border Radius**: 12-16px (rounded corners)
- **Padding**: 16-20px
- **Shadow** (iOS):
  - Offset: 0, 6px
  - Opacity: 0.12-0.22
  - Radius: 8-14px
- **Elevation** (Android): 6-8

#### Buttons

- **Primary Actions**: Teal/Cyan background with white text
- **Secondary Actions**: Outlined with theme colors
- **Destructive Actions**: Red background (#DC3545)
- **Hover State**: Slightly darker shade

#### Icons

- **Size**: 18-20px for primary, 44px for headers
- **Color**: Matches theme accent color
- **Source**: SF Symbols (iOS) / Material Icons (Android)

### Layout Patterns

#### Screen Layout

```
┌─────────────────────┐
│ Safe Area (iOS)     │ ← Status bar + notch safe area
├─────────────────────┤
│ Header              │ ← Title + back/close button
├─────────────────────┤
│ Content             │ ← Scrollable content area
│ (Cards/Lists)       │
├─────────────────────┤
│ Footer/Actions      │ ← Bottom buttons/spacing
└─────────────────────┘
```

#### Card Layout

```
┌──────────────────────────┐
│ ┌──┐ Title       [>]     │ ← Icon + Text + Chevron
│ │  │ Subtitle           │
│ └──┘ Amount    %        │ ← Progress bar
└──────────────────────────┘
```

### Spacing Standards

- **Padding**: 12px, 14px, 16px, 18px, 20px
- **Margin**: 8px, 10px, 12px, 14px, 18px
- **Gap**: 8px, 10px, 12px

### Interactive Elements

#### Press States

- Opacity reduction: 0.7-0.8
- Background color shift: Darker shade (5-10% darker)
- Shadow enhancement: Slight increase

#### Transitions

- Animation duration: 200-300ms
- Easing: Standard (ease-in-out)
- Properties: Background, opacity, transform

### Responsive Design

- **Safe Area Insets**: Automatically applied on iOS (notch/dynamic island support)
- **Portrait Only**: All screens locked to portrait orientation
- **Flexible Layout**: Components scale with screen size
- **Tested Resolutions**: iPhone SE (375px) to iPhone 14 Pro Max (430px)

## 📐 Safe Area Implementation

### Home Screen

- Uses `SafeAreaView` from `react-native-safe-area-context` with `useSafeAreaInsets()`
- Dynamic padding: `paddingTop: insets.top + 10`
- Ensures greeting and hamburger button stay clear of status bar

### Menu Modal

- Uses `SafeAreaView` from `react-native-safe-area-context` for proper modal presentation
- Respects notch and dynamic island
- Additional 10px padding for breathing room

## 🎭 Theme Integration

### Available Themes

All screens automatically adapt to:

- **Light Mode**: Clean, bright, professional
- **Dark Mode**: Easy on the eyes, modern look
- **System Default**: Follows device settings

### Theme Usage

```typescript
const colorScheme = useColorScheme();
const theme = Colors[colorScheme ?? "light"];
const isDark = (colorScheme ?? "light") === "dark";
```

## 🚀 Navigation Architecture

### Routes Structure

```
/
├── index → login
├── login
├── register
├── home (drawer enabled)
├── menu (modal)
├── profile
├── assistant
├── ocr
├── transactions
├── categories
├── reports
├── budget
├── integrations
├── notifications
└── settings
```

### Navigation Patterns

- **Modal Navigation**: Menu opens as overlay
- **Stack Navigation**: Regular screen transitions
- **Back Navigation**: All screens support router.back()
- **Replace Navigation**: Logout uses router.replace() to prevent back

## 🔧 Logout Functionality

**Note**: Logout button is centralized in the Menu only (hamburger menu).

- ✅ Available in: `app/menu.tsx` (Hamburger menu)
- ❌ Removed from: Home, Profile, Settings
- Prevents duplicate logout options across screens
- Creates consistent user experience

## 🎨 Consistency Checklist

Every screen follows:

- ✅ SafeAreaView (from react-native-safe-area-context) or ThemedView wrapper
- ✅ Theme-aware color system
- ✅ Consistent typography
- ✅ 12px border radius for cards
- ✅ Proper shadow/elevation
- ✅ Press state feedback
- ✅ Back/Close button in header
- ✅ Consistent spacing
- ✅ Icon usage from IconSymbol component
- ✅ No duplicate logout buttons

## 🛠️ Development Guidelines

### Adding New Screens

1. Create file in `app/` directory
2. Import theming components
3. Wrap with `ThemedView` or `SafeAreaView` (from react-native-safe-area-context)
4. Use theme colors from `Colors` constant
5. Add route to `app/_layout.tsx`
6. Follow existing screen patterns

### Common Imports

```typescript
import { useColorScheme } from "@/hooks/use-color-scheme";
import { Colors } from "@/constants/theme";
import { ThemedView } from "@/components/themed-view";
import { ThemedText } from "@/components/themed-text";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useSafeAreaInsets } from "react-native-safe-area-context";
```

### Color Usage

```typescript
const colorScheme = useColorScheme();
const theme = Colors[colorScheme ?? "light"];
const isDark = (colorScheme ?? "light") === "dark";

// Apply to components
style={[
  styles.myComponent,
  {
    backgroundColor: theme.cardBackground,
    color: theme.text,
    borderColor: theme.icon
  }
]}
```

## 📦 Dependencies

### Navigation

- `expo-router` - File-based routing
- `@react-navigation/native` - Navigation base
- `@react-navigation/bottom-tabs` - Tab support

### UI & Animations

- `react-native-reanimated` - Smooth animations
- `react-native-gesture-handler` - Gesture support
- `react-native-safe-area-context` - Safe area support
- `expo-symbols` - iOS SF Symbols icons

### Other

- `expo-haptics` - Haptic feedback
- `expo-status-bar` - Status bar configuration

## 📱 Testing Devices

Tested and optimized for:

- iPhone SE (2nd Gen) - 375px width
- iPhone 12/13 - 390px width
- iPhone 14 Pro Max - 430px width
- Samsung Galaxy S21 - 360-412px width
- Tablets - Flexible scaling

## 🎯 Performance Tips

- ✅ Memoized lists with `useMemo`
- ✅ FlatList for long lists (not ScrollView)
- ✅ Efficient animations with Reanimated
- ✅ Theme caching to avoid recalculations
- ✅ Native shadows for better performance

## 🔐 Security Notes

- All screens properly handle authentication state
- Logout uses `router.replace()` to prevent back navigation
- No sensitive data in component state
- Ready for API integration with secure token handling

---

**Last Updated**: November 2025
**Version**: 1.0.0
**Status**: ✅ Production Ready
