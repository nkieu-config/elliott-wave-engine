"use client";

import { useQueryStates } from "nuqs";
import { configParsers } from "@/lib/config";
import { usePipeline } from "@/lib/query";
import { ScenariosPanel } from "@/components/scenarios/scenarios-panel";

// Re-reads the chart's query; TanStack dedupes by cache key, so no second fetch.
export function ScenariosPanelContainer({
  embed = false,
  onCollapse,
}: { embed?: boolean; onCollapse?: () => void } = {}) {
  const [config] = useQueryStates(configParsers);
  const query = usePipeline(config);
  return <ScenariosPanel data={query.data} embed={embed} onCollapse={onCollapse} />;
}
