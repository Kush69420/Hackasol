import { useEffect } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Home } from "./Home";
import { navigate, useLocation } from "./route";
import "./styles.css";

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
