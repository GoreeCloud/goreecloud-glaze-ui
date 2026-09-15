#!/usr/bin/env node
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const CONTRACT_PATH = 'contracts/v1.4.1/human-validation.contract.json';
const TEMPLATE_PATH = 'acceptance/v1.4.1-human-validation.template.json';
const HEX40 = /^[0-9a-f]{40}$/;
const PLACEHOLDERS = new Set(['', 'todo', 'tbd', 'unknown', 'n/a', 'na', 'placeholder', 'example', 'none', 'null']);
const SYNTHETIC_REVIEWER = /^(synthetic|test|example|ci|automation)/i;

class HumanValidationError extends Error {}
function req(condition, message) { if (!condition) throw new HumanValidationError(message); }
function read(relativeOrAbsolute) {
  const path = isAbsolute(relativeOrAbsolute) ? relativeOrAbsolute : resolve(ROOT, relativeOrAbsolute);
  return readFileSync(path, 'utf8');
}
function json(path) {
  let value;
  try { value = JSON.parse(read(path)); }
  catch (error) { throw new HumanValidationError(`invalid JSON ${path}: ${error.message}`); }
  req(value && typeof value === 'object' && !Array.isArray(value), `${path} must contain a JSON object`);
  return value;
}
function meaningful(value, label) {
  req(typeof value === 'string', `${label} must be a string`);
  const text = value.trim();
  req(!PLACEHOLDERS.has(text.toLowerCase()), `${label} contains a placeholder value`);
  req(!text.includes('REPLACE_WITH_'), `${label} contains an unresolved template placeholder`);
  return text;
}
function timestamp(value, label) {
  const text = meaningful(value, label);
  req(/(?:Z|[+-]\d{2}:\d{2})$/.test(text), `${label} must include an explicit timezone`);
  req(!Number.isNaN(Date.parse(text)), `${label} must be ISO-8601`);
  return text;
}
function stringArray(value, label, {allowEmpty = true} = {}) {
  req(Array.isArray(value), `${label} must be an array`);
  if (!allowEmpty) req(value.length > 0, `${label} must not be empty`);
  const seen = new Set();
  for (let index = 0; index < value.length; index += 1) {
    const text = meaningful(value[index], `${label}[${index}]`);
    req(!seen.has(text), `${label} contains duplicate value ${text}`);
    seen.add(text);
  }
  return value;
}
function exactRevision(value, label) {
  const text = meaningful(value, label);
  req(HEX40.test(text), `${label} must be 40 lowercase hex characters`);
  return text;
}

function validateSource() {
  const contract = json(CONTRACT_PATH);
  const template = json(TEMPLATE_PATH);
  const lifecycle = json('registry/lifecycle.json');

  assert.equal(lifecycle.currentStable, '1.4.0', 'V1.4.1 hardening must preserve V1.4.0 Stable authority');
  assert.equal(lifecycle.currentOfficial, '1.4.0', 'V1.4.1 hardening must preserve V1.4.0 Official authority');
  assert.equal(lifecycle.plannedNext, '1.4.1-candidate', 'lifecycle plannedNext must remain 1.4.1-candidate');
  assert.equal(contract.schemaVersion, 2);
  assert.equal(contract.version, '1.4.1-candidate');
  assert.equal(contract.baselineVersion, '1.4.0');
  assert.equal(contract.lifecycle, 'planned-follow-up');
  assert.equal(contract.evidenceAuthority, 'human');
  assert.equal(contract.rules?.automatedEvidenceMaySupportButNeverSatisfyHumanAuthority, true);
  assert.equal(contract.rules?.historicalPassMayCarryForwardOnlyThroughApprovedContinuityAssessment, true);
  assert.equal(contract.rules?.continuityAssessmentMustBindExactSourceAndTargetRevisions, true);
  assert.equal(contract.rules?.continuityAssessmentMustFailClosedOnAffectedOrInconclusiveBehavior, true);
  assert.equal(contract.rules?.continuityAssessmentDoesNotRelabelHistoricalEvidenceAsCurrentRevisionHumanEvidence, true);
  assert.equal(contract.rules?.legacyEvidenceRequiresExactRevisionAndDurableGovernanceAuthorization, true);
  assert.equal(contract.rules?.legacyEvidenceMayNotInventMissingReviewerEnvironmentOrTimestampMetadata, true);
  assert.equal(contract.rules?.promotionRequiresNoPendingBlockedOrFailedChecks, true);
  assert.equal(contract.rules?.v140EvidenceMustNotBeRewritten, true);

  const required = contract.requiredChecks;
  req(Array.isArray(required) && required.length > 0, 'contract must enumerate requiredChecks');
  const ids = required.map((item, index) => meaningful(item?.id, `requiredChecks[${index}].id`));
  req(new Set(ids).size === ids.length, 'requiredChecks ids must be unique');
  for (let index = 0; index < required.length; index += 1) {
    meaningful(required[index].category, `requiredChecks[${index}].category`);
    meaningful(required[index].description, `requiredChecks[${index}].description`);
  }

  assert.equal(template.schemaVersion, 2);
  assert.equal(template.recordType, 'glaze-v1.4.1-human-validation');
  assert.equal(template.glazeUiVersion, '1.4.1');
  assert.equal(template.baselineVersion, '1.4.0');
  assert.equal(template.evidenceType, 'human');
  assert.deepEqual(template.sessions, [], 'template must not manufacture human review sessions');
  assert.deepEqual(template.legacyEvidence, [], 'template must not manufacture legacy evidence');
  assert.deepEqual(template.continuityAssessments, [], 'template must not manufacture continuity decisions');
  assert.equal(template.decision, 'pending', 'template must fail closed');
  assert.equal(template.promotionEligible, false, 'template must never be promotion eligible');

  const hardening = read('GLAZE_UI_V1_4_1_HARDENING.md');
  assert.match(hardening, /Automated evidence may support a review but must not be relabeled as human evidence/i);
  assert.match(hardening, /evidence continuity/i);
  assert.match(hardening, /continuity assessment/i);
  assert.match(hardening, /v1\.4\.1-human-validation\.template\.json/i);
  assert.match(hardening, /verify_glaze_v1_4_1_human_validation\.mjs/i);
  return contract;
}

function validateEnvironment(environment, label) {
  req(environment && typeof environment === 'object' && !Array.isArray(environment), `${label} must be an object`);
  meaningful(environment.platform, `${label}.platform`);
  meaningful(environment.osVersion, `${label}.osVersion`);
  meaningful(environment.device, `${label}.device`);
  meaningful(environment.formFactor, `${label}.formFactor`);
  meaningful(environment.display, `${label}.display`);
  stringArray(environment.inputModalities, `${label}.inputModalities`);
  stringArray(environment.assistiveTechnologies, `${label}.assistiveTechnologies`);
}

function validateResult(result, label, requiredIds) {
  req(result && typeof result === 'object' && !Array.isArray(result), `${label} must be an object`);
  const id = meaningful(result.id, `${label}.id`);
  req(requiredIds.has(id), `${label}.id is not defined by the V1.4.1 human-validation contract`);
  req(['pass', 'fail', 'blocked', 'not_applicable', 'pending'].includes(result.status), `${label}.status is invalid`);
  meaningful(result.scope, `${label}.scope`);
  stringArray(result.limitations, `${label}.limitations`);
  stringArray(result.evidenceRefs, `${label}.evidenceRefs`);
  if (result.status !== 'pending') {
    meaningful(result.finding, `${label}.finding`);
    if (result.status === 'pass' || result.status === 'fail') req(result.evidenceRefs.length > 0, `${id} ${result.status} requires at least one evidence reference`);
    if (result.status === 'not_applicable') req(result.finding.trim().length >= 12, `${id} not_applicable requires an explicit rationale`);
  }
  return id;
}

function validateRecord(record, contract, options = {}) {
  const {promotion = false, expectedRevision = null, allowSynthetic = false} = options;
  assert.equal(record.schemaVersion, 2, 'record schemaVersion must be 2');
  assert.equal(record.recordType, 'glaze-v1.4.1-human-validation', 'recordType mismatch');
  assert.equal(record.glazeUiVersion, '1.4.1', 'glazeUiVersion must be 1.4.1');
  assert.equal(record.baselineVersion, '1.4.0', 'baselineVersion must be 1.4.0');
  assert.equal(record.repository, 'GoreeCloud/goreecloud-glaze-ui', 'repository mismatch');
  assert.equal(record.evidenceType, 'human', 'record evidenceType must be human');
  req(Array.isArray(record.sessions), 'sessions must be an array');
  req(Array.isArray(record.legacyEvidence), 'legacyEvidence must be an array');
  req(Array.isArray(record.continuityAssessments), 'continuityAssessments must be an array');
  req(record.sessions.length + record.legacyEvidence.length > 0, 'record must contain at least one human session or authorized legacy evidence item');
  req(Array.isArray(record.exceptions), 'exceptions must be an array');
  stringArray(record.exceptions, 'exceptions');
  meaningful(record.summary, 'summary');

  if (promotion) {
    req(typeof expectedRevision === 'string' && HEX40.test(expectedRevision), '--promotion requires an explicit 40-character --expected-revision');
    req(record.decision === 'accepted', 'promotion record decision must be accepted');
    req(record.promotionEligible === true, 'promotion record must explicitly set promotionEligible=true');
    req(record.exceptions.length === 0, 'promotion record cannot contain unresolved exceptions');
  } else {
    req(['pending', 'accepted', 'rejected'].includes(record.decision), 'decision must be pending, accepted, or rejected');
    req(typeof record.promotionEligible === 'boolean', 'promotionEligible must be boolean');
  }

  const requiredIds = new Set(contract.requiredChecks.map(item => item.id));
  const evidenceById = new Map([...requiredIds].map(id => [id, []]));
  const sessionIds = new Set();

  for (let sessionIndex = 0; sessionIndex < record.sessions.length; sessionIndex += 1) {
    const session = record.sessions[sessionIndex];
    const prefix = `sessions[${sessionIndex}]`;
    req(session && typeof session === 'object' && !Array.isArray(session), `${prefix} must be an object`);
    const sessionId = meaningful(session.id, `${prefix}.id`);
    req(!sessionIds.has(sessionId), `${prefix}.id must be unique`);
    sessionIds.add(sessionId);
    timestamp(session.reviewedAt, `${prefix}.reviewedAt`);
    const reviewer = meaningful(session.reviewer, `${prefix}.reviewer`);
    meaningful(session.reviewerRole, `${prefix}.reviewerRole`);
    if (!allowSynthetic) req(!SYNTHETIC_REVIEWER.test(reviewer), `${prefix}.reviewer must identify a real human reviewer, not synthetic/automation evidence`);

    req(session.build && typeof session.build === 'object' && !Array.isArray(session.build), `${prefix}.build must be an object`);
    const revision = exactRevision(session.build.sourceRevision, `${prefix}.build.sourceRevision`);
    meaningful(session.build.artifact, `${prefix}.build.artifact`);
    meaningful(session.build.buildIdentifier, `${prefix}.build.buildIdentifier`);
    validateEnvironment(session.environment, `${prefix}.environment`);

    req(Array.isArray(session.results) && session.results.length > 0, `${prefix}.results must contain at least one result`);
    const localIds = new Set();
    for (let resultIndex = 0; resultIndex < session.results.length; resultIndex += 1) {
      const result = session.results[resultIndex];
      const rlabel = `${prefix}.results[${resultIndex}]`;
      const id = validateResult(result, rlabel, requiredIds);
      req(!localIds.has(id), `${prefix} contains duplicate result ${id}`);
      localIds.add(id);
      evidenceById.get(id).push({kind: 'session', status: result.status, sourceRevision: revision, authorityId: sessionId});
    }
  }

  const legacyIds = new Set();
  for (let index = 0; index < record.legacyEvidence.length; index += 1) {
    const item = record.legacyEvidence[index];
    const prefix = `legacyEvidence[${index}]`;
    req(item && typeof item === 'object' && !Array.isArray(item), `${prefix} must be an object`);
    const itemId = meaningful(item.id, `${prefix}.id`);
    req(!legacyIds.has(itemId), `${prefix}.id must be unique`);
    legacyIds.add(itemId);
    const checkId = meaningful(item.checkId, `${prefix}.checkId`);
    req(requiredIds.has(checkId), `${prefix}.checkId is not defined by the V1.4.1 human-validation contract`);
    req(['pass', 'not_applicable'].includes(item.status), `${prefix}.status must be pass or not_applicable`);
    const revision = exactRevision(item.sourceRevision, `${prefix}.sourceRevision`);
    meaningful(item.authorityRef, `${prefix}.authorityRef`);
    meaningful(item.governanceAuthorizationRef, `${prefix}.governanceAuthorizationRef`);
    meaningful(item.scope, `${prefix}.scope`);
    const finding = meaningful(item.finding, `${prefix}.finding`);
    stringArray(item.limitations, `${prefix}.limitations`);
    stringArray(item.provenanceGaps, `${prefix}.provenanceGaps`, {allowEmpty: false});
    stringArray(item.evidenceRefs, `${prefix}.evidenceRefs`, {allowEmpty: false});
    if (item.status === 'not_applicable') req(finding.length >= 12, `${checkId} not_applicable requires an explicit rationale`);
    evidenceById.get(checkId).push({kind: 'legacy', status: item.status, sourceRevision: revision, authorityId: itemId});
  }

  const continuityIds = new Set();
  const continuityByKey = new Map();
  for (let index = 0; index < record.continuityAssessments.length; index += 1) {
    const item = record.continuityAssessments[index];
    const prefix = `continuityAssessments[${index}]`;
    req(item && typeof item === 'object' && !Array.isArray(item), `${prefix} must be an object`);
    const id = meaningful(item.id, `${prefix}.id`);
    req(!continuityIds.has(id), `${prefix}.id must be unique`);
    continuityIds.add(id);
    timestamp(item.assessedAt, `${prefix}.assessedAt`);
    meaningful(item.assessor, `${prefix}.assessor`);
    meaningful(item.assessorRole, `${prefix}.assessorRole`);
    const sourceRevision = exactRevision(item.sourceRevision, `${prefix}.sourceRevision`);
    const targetRevision = exactRevision(item.targetRevision, `${prefix}.targetRevision`);
    req(sourceRevision !== targetRevision, `${prefix} must connect two different exact revisions`);
    req(Array.isArray(item.checkIds) && item.checkIds.length > 0, `${prefix}.checkIds must not be empty`);
    const localChecks = new Set();
    for (let checkIndex = 0; checkIndex < item.checkIds.length; checkIndex += 1) {
      const checkId = meaningful(item.checkIds[checkIndex], `${prefix}.checkIds[${checkIndex}]`);
      req(requiredIds.has(checkId), `${prefix}.checkIds[${checkIndex}] is not canonical`);
      req(!localChecks.has(checkId), `${prefix}.checkIds contains duplicate ${checkId}`);
      localChecks.add(checkId);
    }
    req(['unaffected', 'affected', 'inconclusive'].includes(item.decision), `${prefix}.decision is invalid`);
    const rationale = meaningful(item.rationale, `${prefix}.rationale`);
    req(rationale.length >= 12, `${prefix}.rationale must be substantive`);
    stringArray(item.changedPathsReviewed, `${prefix}.changedPathsReviewed`, {allowEmpty: false});
    stringArray(item.evidenceRefs, `${prefix}.evidenceRefs`, {allowEmpty: false});
    for (const checkId of localChecks) {
      const key = `${sourceRevision}:${targetRevision}:${checkId}`;
      req(!continuityByKey.has(key), `duplicate continuity decision for ${checkId} from ${sourceRevision} to ${targetRevision}`);
      continuityByKey.set(key, {decision: item.decision, assessmentId: id});
    }
  }

  for (const [id, evidence] of evidenceById.entries()) req(evidence.length > 0, `required human-validation check ${id} is missing from all human and legacy evidence`);

  if (record.decision === 'accepted') {
    for (const [id, evidence] of evidenceById.entries()) req(evidence.some(item => ['pass', 'not_applicable'].includes(item.status)), `accepted record has no positive human authority for ${id}`);
    req(record.exceptions.length === 0, 'accepted record cannot contain unresolved exceptions');
  }
  if (record.decision === 'rejected') {
    const hasNegative = [...evidenceById.values()].flat().some(item => ['fail', 'blocked'].includes(item.status));
    req(hasNegative || record.exceptions.length > 0, 'rejected record must identify a failed/blocked check or exception');
    req(record.promotionEligible === false, 'rejected record cannot be promotion eligible');
  }
  if (record.promotionEligible === true) req(record.decision === 'accepted', 'promotionEligible=true requires decision=accepted');

  if (promotion) {
    for (const [id, evidence] of evidenceById.entries()) {
      const direct = evidence.filter(item => item.sourceRevision === expectedRevision);
      req(!direct.some(item => ['fail', 'blocked', 'pending'].includes(item.status)), `${id} contains an unresolved result on exact promotion revision ${expectedRevision}`);
      if (direct.some(item => ['pass', 'not_applicable'].includes(item.status))) continue;
      const historicalPositive = evidence.filter(item => item.sourceRevision !== expectedRevision && ['pass', 'not_applicable'].includes(item.status));
      const carried = historicalPositive.find(item => continuityByKey.get(`${item.sourceRevision}:${expectedRevision}:${id}`)?.decision === 'unaffected');
      req(Boolean(carried), `${id} has no direct positive result on ${expectedRevision} and no approved unaffected continuity assessment from a positive historical result`);
    }
  }

  return {
    sessions: record.sessions.length,
    legacyEvidence: record.legacyEvidence.length,
    continuityAssessments: record.continuityAssessments.length,
    coveredChecks: [...evidenceById.values()].filter(items => items.length > 0).length,
    requiredChecks: requiredIds.size
  };
}

function syntheticRecord(contract, revision = 'a'.repeat(40)) {
  return {
    schemaVersion: 2,
    recordType: 'glaze-v1.4.1-human-validation',
    glazeUiVersion: '1.4.1',
    baselineVersion: '1.4.0',
    repository: 'GoreeCloud/goreecloud-glaze-ui',
    evidenceType: 'human',
    sessions: [{
      id: 'synthetic-format-self-test',
      reviewedAt: '2026-09-13T19:00:00-05:00',
      reviewer: 'synthetic-self-test',
      reviewerRole: 'validator-self-test',
      build: {sourceRevision: revision, artifact: 'synthetic-artifact', buildIdentifier: 'synthetic-build'},
      environment: {platform: 'synthetic-platform', osVersion: 'synthetic-os', device: 'synthetic-device', formFactor: 'synthetic-form-factor', display: 'synthetic-display', inputModalities: [], assistiveTechnologies: []},
      results: contract.requiredChecks.map(check => ({id: check.id, status: 'pass', scope: 'Synthetic structural self-test only; not human evidence.', finding: 'Synthetic pass used only to exercise validator structure; it is not acceptance evidence.', limitations: [], evidenceRefs: ['synthetic://not-human-evidence']}))
    }],
    legacyEvidence: [],
    continuityAssessments: [],
    exceptions: [],
    decision: 'accepted',
    promotionEligible: true,
    summary: 'Synthetic structural validator self-test only; never human acceptance evidence.'
  };
}
function continuity(contract, sourceRevision, targetRevision, decision = 'unaffected') {
  return {
    id: `synthetic-continuity-${decision}`,
    assessedAt: '2026-09-14T18:00:00-05:00',
    assessor: 'synthetic-governance-assessor',
    assessorRole: 'validator-self-test',
    sourceRevision,
    targetRevision,
    checkIds: contract.requiredChecks.map(check => check.id),
    decision,
    rationale: 'Synthetic source-impact assessment used only to exercise fail-closed continuity validation.',
    changedPathsReviewed: ['synthetic/path'],
    evidenceRefs: ['synthetic://continuity-evidence']
  };
}
function expectReject(record, contract, options, label) {
  try { validateRecord(record, contract, options); }
  catch (error) { if (error instanceof HumanValidationError || error instanceof assert.AssertionError) return; throw error; }
  throw new HumanValidationError(`self-test expected rejection for ${label}`);
}
function clone(value) { return JSON.parse(JSON.stringify(value)); }

function selfTest(contract) {
  const target = 'a'.repeat(40);
  const source = 'b'.repeat(40);
  const valid = syntheticRecord(contract, target);
  validateRecord(valid, contract, {promotion: true, expectedRevision: target, allowSynthetic: true});

  const automated = clone(valid); automated.evidenceType = 'automated';
  expectReject(automated, contract, {allowSynthetic: true}, 'automated evidence authority substitution');
  const missing = clone(valid); missing.sessions[0].results.pop();
  expectReject(missing, contract, {allowSynthetic: true}, 'missing required check');
  const pending = clone(valid); pending.sessions[0].results[0].status = 'pending'; pending.sessions[0].results[0].finding = null; pending.sessions[0].results[0].evidenceRefs = [];
  expectReject(pending, contract, {promotion: true, expectedRevision: target, allowSynthetic: true}, 'pending result on promotion revision');
  const noEvidence = clone(valid); noEvidence.sessions[0].results[0].evidenceRefs = [];
  expectReject(noEvidence, contract, {allowSynthetic: true}, 'pass without evidence reference');
  const fakeReviewer = clone(valid);
  expectReject(fakeReviewer, contract, {}, 'synthetic reviewer in real record mode');
  const naWithoutRationale = clone(valid); naWithoutRationale.sessions[0].results[0].status = 'not_applicable'; naWithoutRationale.sessions[0].results[0].finding = 'N/A'; naWithoutRationale.sessions[0].results[0].evidenceRefs = [];
  expectReject(naWithoutRationale, contract, {allowSynthetic: true}, 'not-applicable without rationale');

  const staleWithoutContinuity = syntheticRecord(contract, source);
  expectReject(staleWithoutContinuity, contract, {promotion: true, expectedRevision: target, allowSynthetic: true}, 'historical positive evidence without continuity');
  const carried = syntheticRecord(contract, source); carried.continuityAssessments = [continuity(contract, source, target, 'unaffected')];
  validateRecord(carried, contract, {promotion: true, expectedRevision: target, allowSynthetic: true});
  const affected = clone(carried); affected.continuityAssessments[0].decision = 'affected';
  expectReject(affected, contract, {promotion: true, expectedRevision: target, allowSynthetic: true}, 'affected continuity');
  const inconclusive = clone(carried); inconclusive.continuityAssessments[0].decision = 'inconclusive';
  expectReject(inconclusive, contract, {promotion: true, expectedRevision: target, allowSynthetic: true}, 'inconclusive continuity');
  const wrongTarget = clone(carried); wrongTarget.continuityAssessments[0].targetRevision = 'c'.repeat(40);
  expectReject(wrongTarget, contract, {promotion: true, expectedRevision: target, allowSynthetic: true}, 'continuity bound to wrong target');

  const legacy = clone(valid);
  legacy.sessions = [];
  legacy.legacyEvidence = contract.requiredChecks.map((check, index) => ({
    id: `legacy-${index}`,
    checkId: check.id,
    status: check.id === 'form-factor.watch' ? 'not_applicable' : 'pass',
    sourceRevision: target,
    authorityRef: 'https://github.com/GoreeCloud/goreecloud-glaze-ui/issues/208',
    governanceAuthorizationRef: 'https://github.com/GoreeCloud/goreecloud-glaze-ui/issues/208#option-2',
    scope: 'Synthetic legacy-evidence structural self-test only.',
    finding: check.id === 'form-factor.watch' ? 'Synthetic explicit not-applicable rationale for structural testing only.' : 'Synthetic authorized legacy PASS used only for validator structure testing.',
    limitations: [],
    provenanceGaps: ['Synthetic test omits original environment metadata by design.'],
    evidenceRefs: ['synthetic://legacy-evidence']
  }));
  validateRecord(legacy, contract, {promotion: true, expectedRevision: target, allowSynthetic: true});
  const legacyUnknown = clone(legacy); legacyUnknown.legacyEvidence[0].sourceRevision = 'unknown';
  expectReject(legacyUnknown, contract, {promotion: true, expectedRevision: target, allowSynthetic: true}, 'legacy evidence without exact revision');
}

function parseArgs(argv) {
  const args = {record: null, promotion: false, expectedRevision: null, selfTest: false, sourceOnly: false};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--record') args.record = argv[++index];
    else if (arg === '--promotion') args.promotion = true;
    else if (arg === '--expected-revision') args.expectedRevision = argv[++index];
    else if (arg === '--self-test') args.selfTest = true;
    else if (arg === '--source-only') args.sourceOnly = true;
    else throw new HumanValidationError(`unknown argument ${arg}`);
  }
  if (args.promotion && !args.record) throw new HumanValidationError('--promotion requires --record');
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const contract = validateSource();
  console.log(`GLAZE UI V1.4.1 human-validation source protocol passed (${contract.requiredChecks.length} required checks).`);
  if (args.selfTest) {
    selfTest(contract);
    console.log('Synthetic V1.4.1 validator self-test passed. Synthetic records are not human evidence.');
  }
  if (args.record) {
    const record = json(resolve(process.cwd(), args.record));
    const summary = validateRecord(record, contract, {promotion: args.promotion, expectedRevision: args.expectedRevision});
    console.log(`Validated human record: ${summary.sessions} session(s), ${summary.legacyEvidence} legacy item(s), ${summary.continuityAssessments} continuity assessment(s), ${summary.coveredChecks}/${summary.requiredChecks} required checks covered.`);
    if (args.promotion) console.log(`V1.4.1 human-validation promotion gate passed for exact revision ${args.expectedRevision}.`);
  }
  if (!args.record && !args.selfTest && !args.sourceOnly) console.log('No human record supplied; V1.4.1 human acceptance remains pending.');
}

try { main(); }
catch (error) {
  if (error instanceof HumanValidationError || error instanceof assert.AssertionError) {
    console.error(`GLAZE UI V1.4.1 human-validation verification failed: ${error.message}`);
    process.exit(1);
  }
  throw error;
}
