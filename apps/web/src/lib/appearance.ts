export type AppearancePreferences = {
  accent: "teal" | "blue" | "indigo";
  density: "comfortable" | "compact";
};

export const defaultAppearance: AppearancePreferences = { accent: "teal", density: "comfortable" };

const palettes = {
  teal: { accent: "#087f78", strong: "#066b66", soft: "#e5f4f2" },
  blue: { accent: "#176fa6", strong: "#115a88", soft: "#e7f2f8" },
  indigo: { accent: "#5367b0", strong: "#405292", soft: "#edf0fb" },
};

export function loadAppearance(): AppearancePreferences {
  if (typeof window === "undefined") return defaultAppearance;
  try {
    return { ...defaultAppearance, ...JSON.parse(localStorage.getItem("mr9_appearance") || "{}") };
  } catch {
    return defaultAppearance;
  }
}

export function applyAppearance(preferences: AppearancePreferences) {
  const palette = palettes[preferences.accent] || palettes.teal;
  const root = document.documentElement;
  root.style.setProperty("--mr9-accent", palette.accent);
  root.style.setProperty("--mr9-accent-strong", palette.strong);
  root.style.setProperty("--mr9-accent-soft", palette.soft);
  root.dataset.density = preferences.density;
  localStorage.setItem("mr9_appearance", JSON.stringify(preferences));
}
