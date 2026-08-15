"use client";

import { useState } from "react";
import type { AnalysisResult, SdsExtractResult } from "../types/analisis-log-hp";
import { HpLogsPanel } from "./hp-logs-panel";
import { HpLogsWelcome } from "./hp-logs-welcome";

interface PanelState {
  serial: string;
  modelName: string;
  deviceId: string;
  sdsResult: SdsExtractResult;
  analysis: AnalysisResult;
}

export function HpLogsView() {
  const [panel, setPanel] = useState<PanelState | null>(null);

  function handleResult(
    serial: string,
    modelName: string,
    deviceId: string,
    sdsResult: SdsExtractResult,
    analysis: AnalysisResult,
  ) {
    setPanel({ serial, modelName, deviceId, sdsResult, analysis });
  }

  function handleBack() {
    setPanel(null);
  }

  function handleAnalysisUpdate(analysis: AnalysisResult, sdsResult: SdsExtractResult) {
    if (!panel) return;
    setPanel({ ...panel, analysis, sdsResult });
  }

  if (!panel) {
    return <HpLogsWelcome onResult={handleResult} />;
  }

  return (
    <HpLogsPanel
      serial={panel.serial}
      modelName={panel.modelName}
      deviceId={panel.deviceId}
      sdsResult={panel.sdsResult}
      analysis={panel.analysis}
      onBack={handleBack}
      onAnalysisUpdate={handleAnalysisUpdate}
    />
  );
}
