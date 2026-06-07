import { beforeEach, describe, expect, it } from "vitest";
import { useAskPanel } from "./ask-store";

const reset = () =>
  useAskPanel.setState({ open: false, grounded: false, focusNonce: 0 });

describe("useAskPanel", () => {
  beforeEach(reset);

  it("toggle flips open and bumps focusNonce", () => {
    useAskPanel.getState().toggle();
    expect(useAskPanel.getState().open).toBe(true);
    expect(useAskPanel.getState().focusNonce).toBe(1);
    useAskPanel.getState().toggle();
    expect(useAskPanel.getState().open).toBe(false);
    expect(useAskPanel.getState().focusNonce).toBe(2);
  });

  it("openAsk forces open, presets grounded, bumps nonce", () => {
    useAskPanel.getState().openAsk({ grounded: true });
    const s = useAskPanel.getState();
    expect(s.open).toBe(true);
    expect(s.grounded).toBe(true);
    expect(s.focusNonce).toBe(1);
  });

  it("openAsk without grounded keeps the current grounded value", () => {
    useAskPanel.getState().setGrounded(true);
    useAskPanel.getState().openAsk();
    expect(useAskPanel.getState().grounded).toBe(true);
  });

  it("openAsk re-bumps nonce when already open (re-focus)", () => {
    useAskPanel.getState().openAsk();
    expect(useAskPanel.getState().focusNonce).toBe(1);
    useAskPanel.getState().openAsk();
    expect(useAskPanel.getState().focusNonce).toBe(2);
    expect(useAskPanel.getState().open).toBe(true);
  });

  it("close sets open false without touching grounded", () => {
    useAskPanel.getState().openAsk({ grounded: true });
    useAskPanel.getState().close();
    expect(useAskPanel.getState().open).toBe(false);
    expect(useAskPanel.getState().grounded).toBe(true);
  });
});
