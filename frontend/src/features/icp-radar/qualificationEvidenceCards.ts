import type {
  LiveRadarQualificationResult,
  LiveRadarSourceEvidence,
  QualificationEvidenceFinding,
  QualificationSourceUsage,
} from '../../types';
import { fallbackQualificationSourceUsages } from './liveModel';

// Owns the evidence-card view model used by live qualification rows. It joins
// findings, source usage metadata, and source inventory without exposing raw
// provider artifacts to presentation components.
export type QualificationEvidenceCardView = {
  sourceRef: string;
  sourceName: string;
  sourceUrl: string;
  sourceOrigin: QualificationSourceUsage['source_origin'];
  trustPolicy: QualificationSourceUsage['trust_policy'];
  fact: string;
  excerpt: string;
  excerptType: NonNullable<QualificationEvidenceFinding['excerpt_type']>;
  whyItMatchesRule: string;
  evidenceStrength: QualificationEvidenceFinding['evidence_strength'];
  contradictsRule: boolean;
};

export function qualificationEvidenceCardViews(
  item: LiveRadarQualificationResult,
  sourcesByRef: Map<string, LiveRadarSourceEvidence>,
): QualificationEvidenceCardView[] {
  const sourceUsages = item.source_usages?.length
    ? item.source_usages
    : fallbackQualificationSourceUsages(item, sourcesByRef);
  const usagesByRef = new Map(sourceUsages.map((usage) => [usage.source_ref, usage]));
  const findings = item.evidence_findings?.length
    ? item.evidence_findings
    : fallbackEvidenceFindings(item, sourcesByRef);

  return findings.map((finding) => {
    const usage = usagesByRef.get(finding.source_ref);
    const source = sourcesByRef.get(finding.source_ref);
    return {
      sourceRef: finding.source_ref,
      sourceName: usage?.source_name || source?.title || finding.source_ref,
      sourceUrl: usage?.url || source?.url || '',
      sourceOrigin: usage?.source_origin || 'additional',
      trustPolicy: usage?.trust_policy || (item.confidence === 'high' ? 'trusted' : 'hitl_required'),
      fact: finding.fact || source?.snippet || item.rationale,
      excerpt: finding.excerpt || source?.snippet || '',
      excerptType: finding.excerpt_type || (finding.excerpt ? 'paraphrase' : 'not_available'),
      whyItMatchesRule: finding.why_it_matches_rule || item.rationale,
      evidenceStrength: finding.evidence_strength,
      contradictsRule: finding.contradicts_rule,
    };
  });
}

function fallbackEvidenceFindings(
  item: LiveRadarQualificationResult,
  sourcesByRef: Map<string, LiveRadarSourceEvidence>,
): QualificationEvidenceFinding[] {
  return item.evidence_refs.map((ref) => {
    const source = sourcesByRef.get(ref);
    return {
      source_ref: ref,
      fact: source?.snippet || item.rationale,
      excerpt: '',
      excerpt_type: 'not_available',
      why_it_matches_rule: item.rationale,
      evidence_strength: item.status === 'confirmed' ? 'strong' : item.status === 'weak' ? 'medium' : 'weak',
      contradicts_rule: item.status === 'rejected',
    };
  });
}
