const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export const API_BASE_URL =
  configuredApiBaseUrl ??
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : "");
