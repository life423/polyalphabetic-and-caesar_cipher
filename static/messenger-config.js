// Real-device/local-preview testing uses the same Azure conversations by default.
// Only an explicit localhost development flag selects the isolated local API.
const localDevelopment =
  !window.Capacitor?.isNativePlatform() &&
  ["localhost", "127.0.0.1"].includes(location.hostname) &&
  new URLSearchParams(location.search).get("messenger") === "local";
export const API_BASE = localDevelopment
  ? "http://localhost:8503"
  : "https://ciphercraft-drewclark.azurewebsites.net";
