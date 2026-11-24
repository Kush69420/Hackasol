import { useEffect } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Home } from "./Home";
import { navigate, useLocation } from "./route";
import { getTheme, setTheme } from "./theme";
import "./styles.css";

// Fallback to the inline script in index.html: re-applies the stored theme (dark by default).
setTheme(getTheme());

function Root() {
  const { pathname } = useLocation();
  const isDashboard = pathname === "/dashboard" || pathname === "/dashboard/";
  const isHome = pathname === "/" || pathname === "";

  // Unknown paths fall back to Home, with the address bar corrected to "/".
  useEffect(() => {
    if (!isDashboard && !isHome) navigate("/", true);
  }, [isDashboard, isHome]);

  return isDashboard ? <App /> : <Home />;
}

createRoot(document.getElementById("root")!).render(<Root />);
