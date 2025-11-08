const { getDefaultConfig } = require("@expo/metro-config");
const path = require("path");

const projectRoot = __dirname;

// Ruta hacia la carpeta shared
const sharedPath = path.resolve(projectRoot, "..", "..", "shared");

const config = getDefaultConfig(projectRoot);

// Permitir a Metro vigilar la carpeta shared
config.watchFolders = [sharedPath];

// Hacer que import 'shared' funcione
config.resolver.extraNodeModules = {
  shared: sharedPath,
  ...config.resolver.extraNodeModules,
};

module.exports = config;
