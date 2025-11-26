import { useState } from "react";

export const useSidebar = () => {
  const [isMobileOpen, setMobileOpen] = useState(false);

  return {
    isMobileOpen,
    open: () => setMobileOpen(true),
    close: () => setMobileOpen(false),
    toggle: () => setMobileOpen((prev) => !prev),
  };
};

