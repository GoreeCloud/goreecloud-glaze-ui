import test from 'node:test';
import assert from 'node:assert/strict';
import {QUALIFICATION_WORKSTREAMS, STABLE_QUALIFICATION_WORKSTREAMS, QUALITY_RULE_IDS, evaluateQualificationReadiness, qualificationCandidate} from '../js/glaze-v1.3-qualification.candidate.mjs';

const SOURCE = 'a'.repeat(40);
const OTHER = 'b'.repeat(40);
const EVALUATED_AT = '2026-09-06T18:00:00Z';
const HUMAN_OPTICAL = 'human-optical-and-icon-collision-qualification';
const STABLE_CLEANUP = 'stable-activation-and-source-namespace-cleanup';
const REVIEW_MODE = {
  [HUMAN_OPTICAL]: 'human',
  'manual-assistive-technology-qualification': 'human',
  'physical-device-native-platform-qualification': 'combined',
  'physical-device-production-performance-qualification': 'combined',
  'native-personalization-adapter-qualification': 'combined'
};

function qualityReview(overrides = {}) { return {contract: 'contracts/v1.3/quality-rules.candidate.json', reviewed_rule_ids: [...QUALITY_RULE_IDS], visual_finish_accepted: true, blandness_rejected: true, accessibility_beauty_reviewed: true, responsive_beauty_reviewed: true, critical_final_quality_questions_accepted: true, ...overrides}; }
function record(id, overrides = {}) {
  const base = {schema_version: 2, workstream_id: id, target: {product: 'GLAZE UI V1.3', target_version: '1.3.0-candidate', source_revision: SOURCE}, status: 'passed', observed_at: '2026-09-06T17:00:00Z', valid_until: null, review_authority: {mode: REVIEW_MODE[id], authority: 'authorized qualification review'}, evidence_references: [`evidence/${id}-1`, `evidence/${id}-2`], issues: [], disposition: {accepted_for_lifecycle_gate: true, notes: 'accepted for qualification gate only'}};
  if (id === HUMAN_OPTICAL) base.quality_review = qualityReview();
  return {...base, ...overrides, target: {...base.target, ...(overrides.target ?? {})}, review_authority: {...base.review_authority, ...(overrides.review_authority ?? {})}, disposition: {...base.disposition, ...(overrides.disposition ?? {})}, ...(base.quality_review || overrides.quality_review ? {quality_review: {...(base.quality_review ?? {}), ...(overrides.quality_review ?? {})}} : {})};
}
function completeRecords() { return QUALIFICATION_WORKSTREAMS.map(id => record(id)); }

test('Candidate gate has five workstreams while Stable qualification retains six', () => {
  assert.equal(QUALIFICATION_WORKSTREAMS.length, 5);
  assert.equal(STABLE_QUALIFICATION_WORKSTREAMS.length, 6);
  assert.equal(STABLE_QUALIFICATION_WORKSTREAMS.at(-1), STABLE_CLEANUP);
  assert.equal(QUALIFICATION_WORKSTREAMS.includes(STABLE_CLEANUP), false);
});

test('empty evidence is blocked with all five pre-Candidate workstreams missing', () => {
  const result = evaluateQualificationReadiness([], {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.state, 'blocked');
  assert.equal(result.acceptedWorkstreamCount, 0);
  assert.equal(result.requiredWorkstreamCount, 5);
  assert.equal(result.blockers.length, 5);
});

test('five accepted exact-revision records satisfy only the Candidate qualification gate', () => {
  const result = evaluateQualificationReadiness(completeRecords(), {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.state, 'ready-for-governed-candidate-promotion-review');
  assert.equal(result.qualificationGateSatisfied, true);
  assert.equal(result.acceptedWorkstreamCount, 5);
  assert.equal(result.deferredStableWorkstreamCount, 1);
  assert.equal(result.stableQualificationComplete, false);
  assert.equal(result.lifecyclePromotionGranted, false);
  assert.equal(result.candidateActivated, false);
  assert.equal(result.stablePromoted, false);
  assert.equal(result.accepted[HUMAN_OPTICAL].qualityRuleCount, 55);
});

test('a Stable-cleanup record is not a pre-Candidate prerequisite', () => {
  const stableRecord = {...record(QUALIFICATION_WORKSTREAMS[0]), workstream_id: STABLE_CLEANUP, review_authority: {mode: 'combined', authority: 'release review'}};
  const result = evaluateQualificationReadiness([...completeRecords(), stableRecord], {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.qualificationGateSatisfied, true);
  assert.equal(result.acceptedWorkstreamCount, 5);
  assert.equal(result.accepted[STABLE_CLEANUP], undefined);
});

test('cross-revision Candidate evidence cannot satisfy the exact revision gate', () => {
  const records = completeRecords(); records[0] = record(QUALIFICATION_WORKSTREAMS[0], {target: {source_revision: OTHER}});
  const result = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT});
  assert.equal(result.qualificationGateSatisfied, false); assert.match(result.blockers.join('\n'), /source_revision mismatch/);
});

test('in-progress evidence is not accepted', () => {
  const records = completeRecords(); records[3] = record(QUALIFICATION_WORKSTREAMS[3], {status: 'in_progress', disposition: {accepted_for_lifecycle_gate: false}});
  assert.match(evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT}).blockers.join('\n'), /status is not passed/);
});

test('unresolved issues block Candidate readiness', () => {
  const records = completeRecords(); records[1] = record(QUALIFICATION_WORKSTREAMS[1], {issues: [{summary: 'focus anomaly', severity: 'low', resolved: false}]});
  assert.match(evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT}).blockers.join('\n'), /unresolved issues/);
});

test('human optical qualification cannot be automated-only', () => {
  const records = completeRecords(); records[0] = record(HUMAN_OPTICAL, {review_authority: {mode: 'automated'}});
  assert.match(evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT}).blockers.join('\n'), /review mode automated is not accepted/);
});

test('passed human optical evidence requires all 55 quality rules', () => {
  const records = completeRecords(); records[0] = record(HUMAN_OPTICAL, {quality_review: {reviewed_rule_ids: QUALITY_RULE_IDS.slice(0, 54)}});
  assert.match(evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT}).blockers.join('\n'), /all 55 governed quality rules/);
});

test('visual finish, blandness, accessibility, responsive beauty, and final quality gates fail closed', () => {
  const records = completeRecords(); records[0] = record(HUMAN_OPTICAL, {quality_review: {visual_finish_accepted: false, blandness_rejected: false, accessibility_beauty_reviewed: false, responsive_beauty_reviewed: false, critical_final_quality_questions_accepted: false}});
  const blockers = evaluateQualificationReadiness(records, {sourceRevision: SOURCE, evaluatedAt: EVALUATED_AT}).blockers.join('\n');
  assert.match(blockers, /visual finish gate/); assert.match(blockers, /blandness rejection gate/); assert.match(blockers, /accessibility-as-beauty/); assert.match(blockers, /responsive-beauty/); assert.match(blockers, /final quality test/);
});

test('invalid source revision fails closed', () => {
  const result = evaluateQualificationReadiness(completeRecords(), {sourceRevision: 'not-a-sha', evaluatedAt: EVALUATED_AT});
  assert.equal(result.qualificationGateSatisfied, false); assert.match(result.blockers.join('\n'), /40-character Git SHA/);
});

test('Candidate metadata preserves Proposed lifecycle and Stable-stage separation', () => {
  assert.equal(qualificationCandidate.releaseLifecycle, 'proposed');
  assert.equal(qualificationCandidate.qualificationLifecycle, 'qualification-active');
  assert.equal(qualificationCandidate.qualityRuleCount, 55);
  assert.equal(qualificationCandidate.requiredWorkstreams.length, 5);
  assert.deepEqual([...qualificationCandidate.deferredStableWorkstreams], [STABLE_CLEANUP]);
  assert.equal(qualificationCandidate.canActivateCandidate, false);
  assert.equal(qualificationCandidate.canPromoteStable, false);
  assert.equal(qualificationCandidate.canTreatAutomatedCIAsHumanEvidence, false);
  assert.equal(qualificationCandidate.canTreatAutomatedCIAsPhysicalDeviceEvidence, false);
});
