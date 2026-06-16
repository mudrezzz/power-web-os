import { useEffect, useState } from 'react';
import type { SignalValidationDecision, SignalValidationOverlay } from '../../../types';
import { signalValidationStorageKey } from '../domain/constants';
import { loadSignalValidationOverlay, signalValidationKey } from '../domain/validation';

// Signal decisions are local HITL overlays that never mutate generated demo artifacts.
export function useSignalValidationOverlay() {
  const [signalValidation, setSignalValidation] = useState<SignalValidationOverlay>(() => loadSignalValidationOverlay());

  useEffect(() => {
    if (Object.keys(signalValidation).length) {
      window.localStorage.setItem(signalValidationStorageKey, JSON.stringify(signalValidation));
      return;
    }
    window.localStorage.removeItem(signalValidationStorageKey);
  }, [signalValidation]);

  function saveSignalValidationDecision(decision: SignalValidationDecision) {
    setSignalValidation((current) => ({
      ...current,
      [signalValidationKey(decision.radar_id, decision.account_id, decision.signal_code)]: decision,
    }));
  }

  function resetCandidateSignalValidation(radarId: string, accountId: string) {
    setSignalValidation((current) => Object.fromEntries(
      Object.entries(current).filter(([, decision]) => (
        decision.radar_id !== radarId || decision.account_id !== accountId
      )),
    ));
  }

  function resetSignalValidationDecision(radarId: string, accountId: string, signalCode: string) {
    setSignalValidation((current) => {
      const next = { ...current };
      delete next[signalValidationKey(radarId, accountId, signalCode)];
      return next;
    });
  }

  return {
    signalValidation,
    saveSignalValidationDecision,
    resetCandidateSignalValidation,
    resetSignalValidationDecision,
  };
}
