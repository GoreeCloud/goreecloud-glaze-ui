#!/usr/bin/env node
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {
  StabilizationReviewPacketError,
  assertPacketIsPlanningOnly,
  buildStabilizationReviewPacket
} from './generate_glaze_v1_5_stabilization_review_packet.mjs';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const CONTRACT = resolve(ROOT, 'contracts/v1.5/stabilization-review.dev.json');

function req(condition, message) {
  if (!condition) throw new Error(message);
}

const expectedAreas = [
  'human-usability',
  'assistive-technology-accessibility',
  'target-device-runtime',
  'privacy-authorization',
  'anti-jitter-performance',
  'platform-posture-input-window'
];

const expectedChecks = [
  'human-usability-state-explanations',
  'human-usability-action-stability',
  'human-usability-task-continuity',
  'accessibility-keyboard-focus',
  'accessibility-semantic-announcement',
  'accessibility-presentation-modes',
  'runtime-representative-rendering',
  'runtime-connectivity-continuity',
  'runtime-fallback-integrity',
  'privacy-no-automatic-consent',
  'privacy-diagnostic-minimization',
  'privacy-authority-truthfulness',
  'performance-transition-stability',
  'performance-constrained-mode',
  'performance-representative-budget',
  'platform-posture-continuity',
  'platform-input-fidelity',
  'platform-window-resilience'
];

function buildValidPacket() {
  return buildStabilizationReviewPacket({
    sourceRevision: 'b'.repeat(40),
    artifact: 'glaze-ui-v1.5-development-review',
    buildIdentifier: 'glaze-ui-v1.5-development-review',
    platform: 'web',
    osVersion: 'GoreeCloud review environment',
    runtime: 'browser runtime',
    device: 'GoreeCloud review workstation',
    formFactor: 'desktop',
    display: 'standard review display',
    inputModalities: ['keyboard', 'pointer', 'keyboard'],
    assistiveTechnologies: ['screen-reader', 'screen-reader']
  });
}

function verifyContract() {
  const contract = JSON.parse(readFileSync(CONTRACT, 'utf8'));
  req(contract.schemaVersion === 1, 'contract schema version mismatch');
  req(contract.contractVersion === '1.5.0-dev.1', 'contract version mismatch');
  req(contract.glazeUiVersion === '1.5.0-dev.1', 'Glaze version mismatch');
  req(contract.releaseLifecycle === 'Development', 'lifecycle must remain Development');
  req(contract.stableBaseline === '1.4.1', 'Stable baseline mismatch');
  req(contract.repository === 'GoreeCloud/goreecloud-glaze-ui', 'repository identity mismatch');
  req(contract.authority === 'review-planning-only', 'contract authority must remain review-planning-only');
  req(contract.promotionEligible === false, 'contract cannot be promotion eligible');
  req(contract.consumerEligible === false, 'contract cannot establish consumer eligibility');
  req(contract.releaseCandidate === false, 'contract cannot establish Release Candidate status');
  req(contract.stable === false, 'contract cannot establish Stable status');
  req(Array.isArray(contract.requiredEvidenceAreas), 'requiredEvidenceAreas must be an array');
  req(contract.requiredEvidenceAreas.length === expectedAreas.length, 'required evidence area count mismatch');
  req(contract.requiredEvidenceAreas.map(area => area.id).join('|') === expectedAreas.join('|'), 'required evidence area identity/order mismatch');

  const checks = contract.requiredEvidenceAreas.flatMap(area => area.checks ?? []);
  req(checks.length === expectedChecks.length, 'required stabilization check count mismatch');
  req(checks.map(check => check.id).join('|') === expectedChecks.join('|'), 'required stabilization check identity/order mismatch');
  req(new Set(expectedChecks).size === expectedChecks.length, 'expected stabilization check ids must be unique');
  req(new Set(checks.map(check => check.id)).size === checks.length, 'contract stabilization check ids must be unique');
  req(checks.every(check => typeof check.description === 'string' && check.description.trim().length > 0), 'every stabilization check needs a description');
}

function verifyPacketBoundary() {
  const packet = buildValidPacket();
  assertPacketIsPlanningOnly(packet);
  req(packet.checks.map(check => check.id).join('|') === expectedChecks.join('|'), 'generated packet check identity/order mismatch');
  req(packet.environment.inputModalities.length === 2, 'input modalities must be deduplicated');
  req(packet.environment.assistiveTechnologies.length === 1, 'assistive technologies must be deduplicated');
  req(packet.checks.every(check => check.status === 'pending'), 'generated packet checks must remain pending');
  req(packet.checks.every(check => check.finding === null), 'generated packet must not manufacture findings');
  req(packet.checks.every(check => check.evidenceRefs.length === 0), 'generated packet must not manufacture evidence references');
}

function verifyFailClosedRevisionHandling() {
  let rejected = false;
  try {
    buildStabilizationReviewPacket({
      sourceRevision: 'not-an-exact-revision',
      artifact: 'glaze-ui-v1.5-development-review',
      buildIdentifier: 'glaze-ui-v1.5-development-review',
      platform: 'web',
      osVersion: 'GoreeCloud review environment',
      runtime: 'browser runtime',
      device: 'GoreeCloud review workstation',
      formFactor: 'desktop',
      display: 'standard review display',
      inputModalities: ['keyboard'],
      assistiveTechnologies: []
    });
  } catch (error) {
    rejected = error instanceof StabilizationReviewPacketError;
  }
  req(rejected, 'non-exact source revision must fail closed');
}

verifyContract();
verifyPacketBoundary();
verifyFailClosedRevisionHandling();

console.log('GLAZE UI V1.5 stabilization review development verifier: PASS');
console.log('Coverage: 6 evidence areas / 18 pending review obligations.');
console.log('Boundary: machine verification proves planning-tool integrity only; no external acceptance or lifecycle promotion is established.');
