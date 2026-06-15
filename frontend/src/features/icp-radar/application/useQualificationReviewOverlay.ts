import { useEffect, useState } from 'react';
import type { QualificationReviewDecision } from '../../../types';
import { qualificationReviewStorageKey } from '../domain/constants';
import { loadQualificationReviewOverlay, qualificationReviewKey } from '../domain/qualification';
import type { QualificationReviewOverlay } from '../modelTypes';

// Qualification reviews mirror signal validation for live radar findings.
export function useQualificationReviewOverlay() {
  const [qualificationReview, setQualificationReview] = useState<QualificationReviewOverlay>(() => loadQualificationReviewOverlay());

  useEffect(() => {
    if (Object.keys(qualificationReview).length) {
      window.localStorage.setItem(qualificationReviewStorageKey, JSON.stringify(qualificationReview));
      return;
    }
    window.localStorage.removeItem(qualificationReviewStorageKey);
  }, [qualificationReview]);

  function saveQualificationReviewDecision(
    radarId: string,
    candidateId: string,
    ruleId: string,
    decision: QualificationReviewDecision | null,
  ) {
    const key = qualificationReviewKey(radarId, candidateId, ruleId);
    setQualificationReview((current) => {
      const next = { ...current };
      if (decision) {
        next[key] = decision;
      } else {
        delete next[key];
      }
      return next;
    });
  }

  return { qualificationReview, saveQualificationReviewDecision };
}

