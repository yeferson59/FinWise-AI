# Hamburger Menu Implementation Guide

## Overview
This guide explains the hamburger menu implementation for the FinWise-AI mobile app using Expo Router.

## How It Works

The hamburger menu is implemented as a **modal screen** that appears when you tap the menu button (☰) in the top-right corner of the Home screen.

### Flow:
1. User taps the hamburger menu button in `home.tsx`
2. `router.push("/menu")` navigates to the menu modal screen
3. Menu displays all available navigation options
4. User selects an option or closes the menu
5. Navigation happens and menu closes automatically

## File Structure

```
app/
├── _layout.tsx          # Root layout with Stack Navigator
├── home.tsx             # Home screen with hamburger button
├── menu.tsx             # Menu modal screen
├── profile.tsx
├── assistant.tsx
├── ocr.tsx
├── transactions.tsx
├── categories.tsx
├── reports.tsx
├── budget.tsx
├── integrations.tsx
├── notifications.tsx
├── settings.tsx
├── login.tsx
└── register.tsx
```

## Key Files

### `app/_layout.tsx`
- Uses Expo Router's `Stack` Navigator
- Menu screen is configured as a `modal` presentation
- No theme provider in root layout (prevents drawer conflicts)

### `app/home.tsx`
- Hamburger button uses `router.push("/menu")`
- Button is in the top-right corner of the screen
- Uses `useRouter` from `expo-router`

### `app/menu.tsx`
- Displays all navigation options
- Each menu item navigates using `router.push()` or `router.replace()`
- Close button uses `router.back()` to dismiss the modal
- Logout uses `router.replace("/login")` to prevent back navigation

## Menu Items

The menu includes the following sections:

### Main Navigation
- Perfil (Profile)
- Asistente IA (AI Assistant)
- OCR (Receipt/Invoice Scanning)
- Transacciones (Transactions)
- Categorías (Categories)
- Reportes (Reports)
- Presupuestos (Budget)
- Integraciones (Bank Integrations)
- Notificaciones (Notifications)
- Ajustes (Settings)

### Quick Actions
- Añadir transacción (Add Transaction)
- Generar reporte (Generate Report)

### Authentication
- Cerrar sesión (Logout)

## Styling

The menu adapts to the app's theme:
- **Light mode**: Clean, bright backgrounds
- **Dark mode**: Dark backgrounds with subtle borders

Features:
- Smooth animations (fade + slide up)
- Shadow effects for depth
- Responsive icon sizing
- Color-coded sections

## Navigation Behavior

### Screen Navigation
```typescript
// Push to a new screen
router.push("/profile")

// Replace current screen (for auth)
router.replace("/login")

// Go back to close modal
router.back()
```

### Auto-closing
- Menu automatically closes after navigation
- Uses animation before navigation for smooth UX
- Logout also closes menu before navigating to login

## Dependencies

Required packages:
- `expo-router` - Routing and navigation
- `react-native-gesture-handler` - Gesture support
- `react-native-reanimated` - Animations
- `@react-navigation/native` - Navigation base
- `@react-navigation/bottom-tabs` - Tab navigation (if needed)

## Troubleshooting

### Error: "openDrawer is not a function"
This error indicates drawer navigation is being used somewhere. The current implementation uses a **modal** instead of a drawer, which is simpler and doesn't have this issue.

**Solution:** Ensure you're using the latest `_layout.tsx` which only uses Stack Navigator without ThemeProvider.

### Menu not opening
- Check that `router.push("/menu")` is being called from the button
- Ensure the menu route is registered in `_layout.tsx`
- Verify `presentation: "modal"` is set for the menu screen

### Animations not smooth
- Ensure `react-native-reanimated` is properly installed
- Clear cache: `npx expo start --clear`

## Testing

To test the hamburger menu:

1. **Start the app:**
   ```bash
   cd frontend/mobile
   npm start
   ```

2. **Navigate to home screen**

3. **Tap the hamburger menu button (☰)** in the top-right corner

4. **Verify menu opens as a modal**

5. **Test navigation:**
   - Tap a menu item
   - Verify it navigates to that screen
   - Menu should close automatically

6. **Test close button:**
   - Tap the X button
   - Menu should close without navigation

## Future Improvements

Potential enhancements:
- Add swipe-to-dismiss gesture
- Add search/filter in menu
- Add menu animation customization
- Add menu badges for notifications
- Add user profile info in menu header
- Add menu item icons animations

## Support

If you encounter issues:
1. Clear cache: `npm cache clean --force`
2. Clear Expo cache: `npx expo start --clear`
3. Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
4. Check console for specific error messages
