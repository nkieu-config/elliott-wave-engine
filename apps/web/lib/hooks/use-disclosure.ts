import { useCallback, useId, useState } from "react";

// Headless collapsible: open state + wired ARIA. Spread `triggerProps` on the
// toggle <button>, `contentProps` on the region (then give the region an
// aria-label).
export function useDisclosure(initialOpen = false) {
  const [open, setOpen] = useState(initialOpen);
  const panelId = useId();
  const toggle = useCallback(() => setOpen((o) => !o), []);
  return {
    open,
    setOpen,
    toggle,
    triggerProps: {
      "aria-expanded": open,
      "aria-controls": panelId,
      onClick: toggle,
    },
    contentProps: { id: panelId, role: "region" as const },
  };
}
