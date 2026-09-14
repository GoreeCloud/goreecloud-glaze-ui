#!/usr/bin/env node
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtempSync, readFileSync, rmSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {dirname, isAbsolute, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

import {buildReviewPacket} from './generate_glaze_v1_4_1_review_packet.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const CONTRACT_PATH = resolve(ROOT, 'contracts/v1.4.1/human-validation.contract.json');
const SCHEMA_PATH = resolve(ROOT, 'schemas/v1.4.1-human-review-packet.schema.json');
const HUMAN_VERIFIER = resolve(ROOT, 'scripts/verify_glaze_v1_4_1_human_validation.mjs');
const HEX40 = /^[0-9a-f]{40}$/;

class ReviewPacketVerificationError extends Error {}

function req(condition, message) {
  if (!condition) throw new ReviewPacketVerificationError(message);
}

function json(path) {
  const absolute = isAbsolute(path) ? path : resolve(process.cwd(), path);
  let value;
  try {
    value = JSON.parse(readFileSync(absolute, 'utf8'));
  } catch (error) {
    throw new ReviewPacketVerificationError(`invalid JSON ${path}: ${error.message}`);
  }
  req(value && typeof value === 'object' && !Array.isArray(value), `${path} must contain a JSON object`);
  return value;
}

function nonEmpty(value, label) {
  req(typeof value === 'string' && value.trim().length > 0, `${label} must be a non-empty string`);
  return value.trim();
}

function stringArray(value, label) {
  req(Array.isArray(value), `${label} must be an array`);
  req(new Set(value).size === value.length, `${label} must not contain duplicates`);
  for (let index = 0; index < value.length; index += 1) nonEmpty(value[index], `${label}[${index}]`);
}

function assertForbiddenHumanFields(value, path = '$') {
  if (!value || typeof value !== 'object') return;
  if (Array.isArray(value)) {
    value.forEach((item, index) => assertForbiddenHumanFields(item, `${path}[${index}]`));
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    req(!['recordType', 'evidenceType', 'sessions', 'reviewer', 'reviewerRole', 'reviewedAt', 'decision'].includes(key), `${path}.${key} is a human-evidence authority field and is forbidden in review packets`);
    assertForbiddenHumanFields(child, `${path}.${key}`);
  }
}

function validateSourceParity() {
  const contract = json(CONTRACT_PATH);
  const schema = json(SCHEMA_PATH);
  req(contract.version === '1.4.1-candidate', 'human validation contract must remain V1.4.1 Candidate');
  req(contract.baselineVersion === '1.4.0', 'human validation baseline must remain V1.4.0');
  req(contract.evidenceAuthority === 'human', 'human validation evidence authority must remain human');
  req(Array.isArray(contract.requiredChecks) && contract.requiredChecks.length === 34, 'contract must contain exactly 34 required checks');

  req(schema.$schema === 'https://json-schema.org/draft/2020-12/schema', 'review packet schema must use Draft 2020-12');
  req(schema.properties?.packetType?.const === 'glaze-v1.4.1-human-review-packet', 'review packet schema type mismatch');
  req(schema.properties?.authority?.const === 'pre-review-planning-only', 'review packet schema authority mismatch');
  req(schema.properties?.promotionEligible?.const === false, 'review packet schema must force promotionEligible=false');
  req(schema.properties?.checks?.minItems === 34 && schema.properties?.checks?.maxItems === 34, 'review packet schema must require exactly 34 checks');
  req(schema.properties?.checks?.items?.properties?.status?.const === 'pending', 'review packet schema must force pending check status');
  req(schema.properties?.checks?.items?.properties?.finding?.const === null, 'review packet schema must prohibit generated findings');

  const contractIds = contract.requiredChecks.map(check => check.id);
  const schemaIds = schema.properties?.checks?.items?.properties?.id?.enum;
  req(Array.isArray(schemaIds), 'review packet schema must enumerate check ids');
  assert.deepEqual(schemaIds, contractIds, 'review packet schema check ids must exactly match canonical contract order');
  req(new Set(schemaIds).size === 34, 'review packet schema check ids must be unique');
  return contract;
}

function validatePacket(packet, contract) {
  req(packet.schemaVersion === 1, 'packet schemaVersion must be 1');
  req(packet.packetType === 'glaze-v1.4.1-human-review-packet', 'packetType mismatch');
  req(packet.glazeUiVersion === '1.4.1', 'glazeUiVersion must be 1.4.1');
  req(packet.baselineVersion === '1.4.0', 'baselineVersion must be 1.4.0');
  req(packet.repository === 'GoreeCloud/goreecloud-glaze-ui', 'repository mismatch');
  req(packet.authority === 'pre-review-planning-only', 'packet authority must be pre-review-planning-only');
  req(typeof packet.sourceRevision === 'string' && HEX40.test(packet.sourceRevision), 'packet sourceRevision must be exact 40 lowercase hex');
  req(packet.promotionEligible === false, 'review packet can never be promotion eligible');
  nonEmpty(packet.notice, 'notice');
  req(/not human evidence/i.test(packet.notice), 'notice must state the packet is not human evidence');

  req(packet.build && typeof packet.build === 'object' && !Array.isArray(packet.build), 'build must be an object');
  nonEmpty(packet.build.artifact, 'build.artifact');
  nonEmpty(packet.build.buildIdentifier, 'build.buildIdentifier');

  const environment = packet.environment;
  req(environment && typeof environment === 'object' && !Array.isArray(environment), 'environment must be an object');
  nonEmpty(environment.platform, 'environment.platform');
  nonEmpty(environment.osVersion, 'environment.osVersion');
  nonEmpty(environment.device, 'environment.device');
  nonEmpty(environment.formFactor, 'environment.formFactor');
  nonEmpty(environment.display, 'environment.display');
  stringArray(environment.inputModalities, 'environment.inputModalities');
  stringArray(environment.assistiveTechnologies, 'environment.assistiveTechnologies');

  req(Array.isArray(packet.checks) && packet.checks.length === 34, 'packet must contain exactly 34 checks');
  const requiredById = new Map(contract.requiredChecks.map(check => [check.id, check]));
  const ids = new Set();
  for (let index = 0; index < packet.checks.length; index += 1) {
    const check = packet.checks[index];
    const label = `checks[${index}]`;
    req(check && typeof check === 'object' && !Array.isArray(check), `${label} must be an object`);
    req(requiredById.has(check.id), `${label}.id is not canonical`);
    req(!ids.has(check.id), `${label}.id is duplicated`);
    ids.add(check.id);
    const canonical = requiredById.get(check.id);
    req(check.category === canonical.category, `${label}.category drifted from contract`);
    req(check.description === canonical.description, `${label}.description drifted from contract`);
    req(check.status === 'pending', `${label}.status must remain pending`);
    req(check.finding === null, `${label}.finding must remain null before human review`);
    req(Array.isArray(check.limitations) && check.limitations.length === 0, `${label}.limitations must start empty`);
    req(Array.isArray(check.evidenceRefs) && check.evidenceRefs.length === 0, `${label}.evidenceRefs must start empty`);
  }
  req(ids.size === 34, 'packet must cover every canonical review check exactly once');
  assertForbiddenHumanFields(packet);
  return {checks: ids.size};
}

function proveHumanVerifierRejects(packet) {
  const temp = mkdtempSync(resolve(tmpdir(), 'glaze-v141-review-packet-'));
  try {
    const packetPath = resolve(temp, 'packet.json');
    writeFileSync(packetPath, JSON.stringify(packet, null, 2) + '\n', 'utf8');
    const result = spawnSync(process.execPath, [HUMAN_VERIFIER, '--record', packetPath], {
      cwd: ROOT,
      encoding: 'utf8'
    });
    req(result.status !== 0, 'human-evidence verifier unexpectedly accepted a review planning packet');
    const output = `${result.stdout || ''}\n${result.stderr || ''}`;
    req(/human-validation verification failed/i.test(output), 'human verifier rejection did not use its fail-closed path');
  } finally {
    rmSync(temp, {recursive: true, force: true});
  }
}

function syntheticPacket() {
  return buildReviewPacket({
    sourceRevision: 'a'.repeat(40),
    artifact: 'synthetic-review-build.apk',
    buildIdentifier: 'synthetic-review-build',
    platform: 'android',
    osVersion: 'synthetic-os',
    device: 'synthetic-device',
    formFactor: 'mobile',
    display: 'synthetic-display',
    inputModalities: ['touch'],
    assistiveTechnologies: []
  });
}

function selfTest(contract) {
  const packet = syntheticPacket();
  validatePacket(packet, contract);
  proveHumanVerifierRejects(packet);

  const mutated = JSON.parse(JSON.stringify(packet));
  mutated.checks[0].status = 'pass';
  assert.throws(() => validatePacket(mutated, contract), ReviewPacketVerificationError);

  const reviewer = JSON.parse(JSON.stringify(packet));
  reviewer.reviewer = 'synthetic-human';
  assert.throws(() => validatePacket(reviewer, contract), ReviewPacketVerificationError);

  const promotion = JSON.parse(JSON.stringify(packet));
  promotion.promotionEligible = true;
  assert.throws(() => validatePacket(promotion, contract), ReviewPacketVerificationError);
}

function parseArgs(argv) {
  const args = {packet: null, selfTest: false, sourceOnly: false};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--packet') args.packet = argv[++index];
    else if (arg === '--self-test') args.selfTest = true;
    else if (arg === '--source-only') args.sourceOnly = true;
    else throw new ReviewPacketVerificationError(`unknown argument ${arg}`);
  }
  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const contract = validateSourceParity();
  console.log('GLAZE UI V1.4.1 review-packet contract/schema parity: PASS (34 checks).');

  if (args.selfTest) {
    selfTest(contract);
    console.log('Review-packet fail-closed self-test: PASS; human-evidence verifier rejects planning packets.');
  }

  if (args.packet) {
    const packet = json(args.packet);
    const summary = validatePacket(packet, contract);
    proveHumanVerifierRejects(packet);
    console.log(`Validated pre-review packet: ${summary.checks}/34 checks pending; packet remains non-evidence and promotion-ineligible.`);
  }

  if (!args.packet && !args.selfTest && !args.sourceOnly) {
    console.log('No review packet supplied; source parity only. No human acceptance is implied.');
  }
}

try {
  main();
} catch (error) {
  if (error instanceof ReviewPacketVerificationError || error instanceof assert.AssertionError) {
    console.error(`GLAZE UI V1.4.1 review-packet verification failed: ${error.message}`);
    process.exit(1);
  }
  throw error;
}
