"use client";

import { useQuery, useQueryClient, type UseQueryResult } from "@tanstack/react-query";
import { useEffect } from "react";
import { fetchEducation, fetchLayer1, fetchPipeline, type PipelineConfig } from "./api";
import type { FamilyEducation, Layer1Result, SampleData } from "./types";

const FIVE_MINUTES = 5 * 60 * 1000;

export function usePipeline(
  config: PipelineConfig,
): UseQueryResult<SampleData, Error> {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ["pipeline", config],
    queryFn: ({ signal }) => fetchPipeline(config, signal),
    staleTime: FIVE_MINUTES,
    // Keep prior chart while a new config fetches — avoids slider-tick flicker.
    placeholderData: (prev) => prev,
    retry: 1,
  });

  // Warm the Layer-1 cache from the embedded payload to avoid a first-paint
  // waterfall; only non-top-scenario selections then hit the network.
  const top = query.data?.top_scenario;
  const embedded = query.data?.top_scenario_layer1;
  useEffect(() => {
    if (!top || !embedded) return;
    qc.setQueryData<Layer1Result>(["layer1", config, top.id], embedded);
    // Stable primitives only — `config` gets a fresh identity each render, but RQ
    // hashes the queryKey structurally so the cache write stays keyed right.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [top?.id, embedded, qc]);

  return query;
}

// Cached per (config × scenario_id) so all consumers share one response.
export function useLayer1(
  config: PipelineConfig,
  scenarioId: string | null | undefined,
): UseQueryResult<Layer1Result, Error> {
  return useQuery({
    queryKey: ["layer1", config, scenarioId],
    queryFn: ({ signal }) =>
      fetchLayer1({ ...config, scenario_id: scenarioId as string }, signal),
    enabled: Boolean(scenarioId),
    staleTime: FIVE_MINUTES,
    // Same scenario only — never show another's targets.
    placeholderData: (prev) =>
      prev && prev.scenario_id === scenarioId ? prev : undefined,
    retry: 1,
  });
}

// staleTime Infinity — never changes in a session.
export function useEducation(
  family: string | null | undefined,
): UseQueryResult<FamilyEducation, Error> {
  return useQuery({
    queryKey: ["education", family],
    queryFn: ({ signal }) => fetchEducation(family as string, signal),
    enabled: Boolean(family),
    staleTime: Infinity,
    retry: 1,
  });
}
