import { useCallback, useEffect, useState } from "react";

export type Theme = "dark" | "light";

const KEY = "dpdp-theme";
const listeners = new Set<(theme: Theme) => void>();

/** Dark is the default. Only an explicitly stored "light" yields light; any other value, or no storage, yields dark. */
export function getTheme(): Theme {
  try {
    return window.localStorage.getItem(KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function setTheme(theme: Theme) {
  try { window.localStorage.setItem(KEY, theme); } catch { /* storage unavailable */ }
  document.documentElement.dataset.theme = theme;
  listeners.forEach((listener) => listener(theme));
}

/** Current theme plus a toggle. Every component using the hook on the same page stays in sync. */
export function useTheme(): [Theme, () => void] {
  const [theme, setLocal] = useState<Theme>(getTheme);

  useEffect(() => {
    listeners.add(setLocal);
    return () => { listeners.delete(setLocal); };
  }, []);

  const toggle = useCallback(() => setTheme(getTheme() === "dark" ? "light" : "dark"), []);
  return [theme, toggle];
}
