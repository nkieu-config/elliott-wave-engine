"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { toast } from "sonner";

// Stable id so Sonner reuses one slot instead of stacking on rapid R presses.
const REFRESH_TOAST_ID = "ewl-refresh-pipeline";

// toast.promise so the toast tracks the refetch lifecycle.
export function useRefreshPipeline() {
  const queryClient = useQueryClient();
  return useCallback(() => {
    void toast.promise(
      queryClient.refetchQueries({ queryKey: ["pipeline"] }),
      {
        id: REFRESH_TOAST_ID,
        loading: "Refreshing pipeline…",
        success: "Pipeline updated",
        error: (err: unknown) =>
          err instanceof Error ? `Refresh failed: ${err.message}` : "Refresh failed",
      },
    );
  }, [queryClient]);
}
