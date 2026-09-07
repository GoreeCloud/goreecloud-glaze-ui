import test from 'node:test';
import assert from 'node:assert/strict';

import {
  QUALIFICATION_WORKSTREAMS,
  evaluateQualificationReadiness,
  qualificationCandidate
} from '../js/glaze-v1.3-qualification.candidate.mjs';

const SOURCE = 'a'.repeat(40);
const OTHER = 'b'.repeat(40);
const EVALUATED_AT = '2026-09-06T18:00:00Z';

const REVIEW_MODE = {
  'human-optical-and-icon-collision-qualification': 'human',
  'manual-assistive-technology-qualification': 'human',
  'physical-device-native-platform-qualification': 'combined',
  'physical-device-production-performance-qualification': 'combined',
  'native-personalization-adapter-qualification': 'combined',
  'stable-activation-and-source-namespace-cleanup': 'combined'
};

function record(workstreamId, overrides = {}) {
  const base = {
    schema_version: 1,
    workstream_id: workstreamId,
    target: {
      product: 'GLAZE UI V1.3',
      target_version: '1.3.0-candidate',
      source_revision: SOURCE
    },
    status: 'passed',
    observed_at: '2026-09-06T17:00:00Z',
    valid_until: null,
    review_authority: {
      mode: REVIEW_MODE[workstreamId],
      authority: 'authorized qualification review'
    },
    evidence_references: [`evidence/${workstreamId}-1`, `evidence/${workstreamId}-2`],
    issues: [],
    disposition: {
      accepted_for_lifecycle_gate: true,
      notes: 'accepted for qualification gate only'
    }
  };
  return {
    ...base,
    ...overrides,
    target: {...base.target, ...(overrides.target ?? {})},
    review_authority: {...base.review_authority, ...(overrides.review_authority ?? {})},
    disposition: {...base.disposition, ...(overrides.disposition ?? {})}
  };
}

function completeRecords() {
  return QUALIFICATION_WORKSTREAMS.map(id => record(id));
}

test('empty evidence is blocked with all six workstreams missing', () => {
  const result = evaluateQualificationReadiness([], {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.state, 'blocked');
  assert.equal(result.acceptedWorkstreamCount, 0);
  assert.equal(result.blockers.length, 6);
});

test('six accepted exact-revision records satisfy only the qualification gate', () => {
  const result = evaluateQualificationReadiness(completeRecords(), {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.state, 'ready-for-governed-candidate-promotion-review');
  assert.equal(result.qualificationGateSatisfied, true);
  assert.equal(result.acceptedWorkstreamCount, 6);
  assert.equal(result.lifecyclePromotionGranted, false);
  assert.equal(result.candidateActivated, false);
});

test('qualification readiness never grants consumer eligibility or conformance', () => {
  const result = evaluateQualificationReadiness(completeRecords(), {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.consumerEligibilityGranted, false);
  assert.equal(result.consumerConformanceGranted, false);
});

test('cross-revision evidence cannot satisfy the exact revision gate', () => {
  const records = completeRecords();
  records[0] = record(QUALIFICATION_WORKSTREAMS[0], {target: {source_revision: OTHER}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.qualificationGateSatisfied, false);
  assert.match(result.blockers.join('\n'), /source_revision mismatch/);
});

test('wrong target product fails closed', () => {
  const records = completeRecords();
  records[1] = record(QUALIFICATION_WORKSTREAMS[1], {target: {product: 'GLAZE UI V1.2'}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /target\.product mismatch/);
});

test('wrong target version fails closed', () => {
  const records = completeRecords();
  records[2] = record(QUALIFICATION_WORKSTREAMS[2], {target: {target_version: '1.3.0'}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /target\.target_version mismatch/);
});

test('in-progress evidence is not accepted', () => {
  const records = completeRecords();
  records[3] = record(QUALIFICATION_WORKSTREAMS[3], {status: 'in_progress', disposition: {accepted_for_lifecycle_gate: false}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /status is not passed/);
});

test('failed evidence is not accepted', () => {
  const records = completeRecords();
  records[4] = record(QUALIFICATION_WORKSTREAMS[4], {status: 'failed', disposition: {accepted_for_lifecycle_gate: false}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /status is not passed/);
});

test('passed evidence without lifecycle-gate acceptance is blocked', () => {
  const records = completeRecords();
  records[5] = record(QUALIFICATION_WORKSTREAMS[5], {disposition: {accepted_for_lifecycle_gate: false}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /not accepted for lifecycle gate/);
});

test('expired evidence is blocked', () => {
  const records = completeRecords();
  records[0] = record(QUALIFICATION_WORKSTREAMS[0], {valid_until: '2026-09-06T16:59:59Z'});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /record is expired/);
});

test('unresolved issues block lifecycle-gate readiness regardless of severity', () => {
  const records = completeRecords();
  records[1] = record(QUALIFICATION_WORKSTREAMS[1], {
    issues: [{summary: 'focus order anomaly', severity: 'low', resolved: false}]
  });
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /unresolved issues/);
});

test('human optical qualification cannot be satisfied by automated-only review', () => {
  const records = completeRecords();
  records[0] = record(QUALIFICATION_WORKSTREAMS[0], {review_authority: {mode: 'automated'}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /review mode automated is not accepted/);
});

test('physical-device qualification requires combined review authority', () => {
  const records = completeRecords();
  records[2] = record(QUALIFICATION_WORKSTREAMS[2], {review_authority: {mode: 'human'}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.match(result.blockers.join('\n'), /review mode human is not accepted/);
});

test('a superseded record does not block when a newer valid passed record exists', () => {
  const id = QUALIFICATION_WORKSTREAMS[0];
  const records = completeRecords();
  records.push(record(id, {
    status: 'superseded',
    observed_at: '2026-09-06T16:00:00Z',
    disposition: {accepted_for_lifecycle_gate: false}
  }));
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.qualificationGateSatisfied, true);
});

test('invalid source revision fails closed before evidence aggregation', () => {
  const result = evaluateQualificationReadiness(completeRecords(), {sourceRevision: 'not-a-sha', evaluatedAt: EVALUATED_AT});
  assert.equal(result.qualificationGateSatisfied, false);
  assert.match(result.blockers.join('\n'), /40-character Git SHA/);
});

test('candidate metadata preserves Proposed lifecycle and non-activation permissions', () => {
  assert.equal(qualificationCandidate.releaseLifecycle, 'proposed');
  assert.equal(qualificationCandidate.qualificationLifecycle, 'qualification-active');
  assert.equal(qualificationCandidate.consumerEligible, false);
  assert.equal(qualificationCandidate.canActivateCandidate, false);
  assert.equal(qualificationCandidate.canChangeLifecycleRegistry, false);
  assert.equal(qualificationCandidate.canChangeVersionFile, false);
  assert.equal(qualificationCandidate.canTreatAutomatedCIAsHumanEvidence, false);
  assert.equal(qualificationCandidate.canTreatAutomatedCIAsPhysicalDeviceEvidence, false);
});
