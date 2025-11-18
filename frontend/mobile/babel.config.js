// Babel configuration for the mobile (Expo) app.
// This enables the Reanimated 2 babel plugin which MUST be listed
// as the last plugin in the configuration.
module.exports = function (api) {
  api.cache(true);

  return {
    presets: [
      // Use Expo preset if your project uses Expo
      "babel-preset-expo",
      // If you're not using Expo, replace the line above with:
      // "module:metro-react-native-babel-preset"
    ],
    plugins: [
      // Add other plugins here if needed (they must come BEFORE reanimated plugin)
      // e.g. ["@babel/plugin-proposal-decorators", { "legacy": true }],
      // IMPORTANT: react-native-reanimated plugin must be last
      "react-native-reanimated/plugin"
    ],
  };
};
