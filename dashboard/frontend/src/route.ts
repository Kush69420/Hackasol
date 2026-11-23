import { useEffect, useState } from "react";

// A tiny History-API path switch: no router dependency. Paths are "/" (Home) and "/dashboard".

export type Location = { pathname: string; search: string };

function readLocation(): Location {
  return { pathname: window.location.pathname, search: window.location.search };
}

/** Changes the URL without a page load and tells every mounted subscriber to re-read it. */
export function navigate(to: string, replace = false) {
  if (replace) window.history.replaceState(null, "", to);
  else window.history.pushState(null, "", to);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

/** Current pathname and query string; updates on back/forward and on navigate(). */
export function useLocation(): Location {
  const [loc, setLoc] = useState<Location>(readLocation);
  useEffect(() => {
    const sync = () => setLoc(readLocation());
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  return loc;
}
